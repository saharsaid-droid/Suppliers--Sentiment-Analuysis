import os
import yaml
import mysql.connector as my
import smtplib
import traceback
from email.mime.text import MIMEText
from logging_confg import setup_logger

alert_logger = setup_logger("alert_logger")
email_logger = setup_logger("email_logger")


def load_district_negative_alerts(config_path):
    conn = None
    cursor = None

    try:
        config_path = os.path.join(os.path.dirname(__file__), config_path)
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)

        if "db" not in config or "alert_threshold" not in config:
            raise KeyError("Missing 'db' or 'alert_threshold' in configuration file")

        db_conf = config["db"]
        threshold = config["alert_threshold"]

        conn = my.connect(
            host=db_conf["host"],
            user=db_conf["user"],
            password=db_conf["password"],
            database=db_conf["database"],
        )
        cursor = conn.cursor()
        alert_logger.info("Connected to database successfully")

        cursor.execute(
            "SELECT district_id, governorate, district, num_negative FROM district_stats"
        )
        districts = cursor.fetchall()

        if not districts:
            alert_logger.warning("No districts found in district_stats table.")
            return []

        for district_id, governorate, district, num_neg in districts:
            cursor.execute(
                "SELECT num_negative, status FROM notifications WHERE district_id=%s",
                (district_id,),
            )
            res = cursor.fetchone()
            alert_message = f"Alert: District '{district}' in {governorate} has {num_neg} negative reviews."

            if res:
                prev_num, status = res
                if status == "no" and num_neg >= threshold:
                    cursor.execute(
                        "UPDATE notifications SET num_negative=%s, status='yes', alert_message=%s WHERE district_id=%s",
                        (num_neg, alert_message, district_id),
                    )
                else:
                    cursor.execute(
                        "UPDATE notifications SET num_negative=%s, alert_message=%s WHERE district_id=%s AND status='no'",
                        (num_neg, alert_message, district_id),
                    )
            else:
                status_val = "yes" if num_neg >= threshold else "no"
                cursor.execute(
                    "INSERT INTO notifications(district_id,num_negative,threshold,status,alert_message) VALUES(%s,%s,%s,%s,%s)",
                    (district_id, num_neg, threshold, status_val, alert_message),
                )

        conn.commit()
        alert_logger.info("Notifications updated successfully")

        cursor.execute(
            "SELECT district_id, alert_message FROM notifications WHERE status='yes'"
        )
        pending_alerts = cursor.fetchall()
        alerts = [
            {"district_id": row[0], "alert_message": row[1]} for row in pending_alerts
        ]
        alert_logger.info(f"{len(alerts)} alert(s) ready to send")
        return alerts

    except (FileNotFoundError, KeyError, my.Error, yaml.YAMLError) as e:
        alert_logger.error(f"Alert generation failed: {e}")
        alert_logger.debug(traceback.format_exc())
        raise
    except Exception as e:
        alert_logger.critical(f"Unexpected error: {e}")
        alert_logger.debug(traceback.format_exc())
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        alert_logger.info("Database connection closed")


def send_district_alert_emails(alerts, config):
    try:
        if not alerts:
            email_logger.info("No pending alerts to send.")
            return

        required_keys = ["email", "email_password", "email_to"]
        for key in required_keys:
            if key not in config:
                raise KeyError(f"Missing required configuration key: '{key}'")

        email_user = config["email"]
        email_password = config["email_password"]
        email_to = config["email_to"]

        if not isinstance(email_to, list) or not email_to:
            raise ValueError("'email_to' must be a non-empty list of recipients.")

        smtp = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15)
        smtp.login(email_user, email_password)
        email_logger.info("Connected to SMTP server successfully")

        sent_count = 0
        for alert in alerts:
            try:
                msg = MIMEText(alert["alert_message"], "plain", "utf-8")
                msg["Subject"] = (
                    f"Negative Review Alert - District {alert['district_id']}"
                )
                msg["From"] = email_user
                msg["To"] = ", ".join(email_to)
                smtp.send_message(msg)
                sent_count += 1
                email_logger.info(
                    f"Alert email sent for district {alert['district_id']}"
                )
            except Exception as e:
                email_logger.warning(
                    f"Failed to send alert for district {alert.get('district_id')}: {e}"
                )

        smtp.quit()
        email_logger.info(f"Successfully sent {sent_count} alert email(s).")

    except (KeyError, ValueError, smtplib.SMTPException) as e:
        email_logger.error(f"Email sending failed: {e}")
        email_logger.debug(traceback.format_exc())
        raise
    except Exception as e:
        email_logger.critical(f"Unexpected error while sending emails: {e}")
        email_logger.debug(traceback.format_exc())
        raise
