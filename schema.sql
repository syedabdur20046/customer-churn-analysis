CREATE DATABASE IF NOT EXISTS customer_churn;
USE customer_churn;

DROP TABLE IF EXISTS db_support;
DROP TABLE IF EXISTS db_subscription;
DROP TABLE IF EXISTS db_customer;

CREATE TABLE db_customer (
    customerid INT PRIMARY KEY,
    name       VARCHAR(100),
    country    VARCHAR(50),
    State      VARCHAR(50),
    gender     VARCHAR(10),
    dob        DATE,
    interests  VARCHAR(100),
    pincode    VARCHAR(10)
);

CREATE TABLE db_subscription (
    customerid              INT PRIMARY KEY,
    subscription_start_date DATE,
    subscription_type       VARCHAR(30),
    renewal_date            DATE,
    plan_type               VARCHAR(20),   -- Basic / Standard / Premium
    contract_type           VARCHAR(20),   -- Monthly / Annual
    cancellation_date       DATE NULL,
    cancellation_reason     VARCHAR(50) NULL,
    monthly_charges         DECIMAL(10,2),
    cltv                    DECIMAL(12,2),
    churn_score             INT,
    FOREIGN KEY (customerid) REFERENCES db_customer(customerid)
);

CREATE TABLE db_support (
    complaint_id   INT AUTO_INCREMENT PRIMARY KEY,
    customerid     INT,
    complaint_date DATE,
    Escalations    TINYINT,               -- 1 = escalated, 0 = not
    csat_score     TINYINT,
    col_1          VARCHAR(30),
    comment        VARCHAR(255),
    FOREIGN KEY (customerid) REFERENCES db_customer(customerid)
);
