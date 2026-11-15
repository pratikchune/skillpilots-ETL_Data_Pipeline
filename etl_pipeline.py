
import mysql.connector
import pandas as pd



try:
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="etl_project"
    )

    print("MySQL Connected Successfully!")

   
    query = "SELECT * FROM sales_data"

    df = pd.read_sql_query(query, connection)

    print("\nOriginal Data:")
    print(df)

    print("\nOriginal Records:", len(df))

    df = df.drop_duplicates()

    # Remove extra spaces
    text_columns = [
        "customer_name", "city", "product", "email"
    ]

    for column in text_columns:
        df[column] = df[column].apply(
            lambda x: x.strip() if isinstance(x, str) else x
        )

    # Handle missing values
    df["customer_name"] = df["customer_name"].fillna("Unknown")
    df["city"] = df["city"].fillna("Unknown")
    df["product"] = df["product"].fillna("Unknown")
    df["email"] = df["email"].fillna("Not Available")

    df["quantity"] = df["quantity"].fillna(0)

    # Convert data types
    df["quantity"] = df["quantity"].astype(int)
    df["unit_price"] = pd.to_numeric(
        df["unit_price"], errors="coerce"
    ).fillna(0)

    df["order_date"] = pd.to_datetime(
        df["order_date"], errors="coerce"
    )

    # Create total sales column
    df["total_sales"] = (
        df["quantity"] * df["unit_price"]
    )

    # Remove invalid dates
    df = df.dropna(subset=["order_date"])

    # Convert date into MySQL-compatible format
    df["order_date"] = df["order_date"].dt.date

    print("\nCleaned Data:")
    print(df)

    print("\nCleaned Records:", len(df))


    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cleaned_sales (
            id INT PRIMARY KEY,
            customer_name VARCHAR(100),
            city VARCHAR(100),
            product VARCHAR(100),
            quantity INT,
            unit_price DECIMAL(10,2),
            order_date DATE,
            email VARCHAR(150),
            total_sales DECIMAL(12,2)
        )
    """)

    # Clear previous output to avoid duplicate loading
    cursor.execute("DELETE FROM cleaned_sales")


    insert_query = """
        INSERT INTO cleaned_sales
        (id, customer_name, city, product,
         quantity, unit_price, order_date,
         email, total_sales)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    data = []

    for row in df.itertuples(index=False, name=None):
            data.append(tuple(value.item() if hasattr(value, "item") else value
        for value in row
    ))

    cursor.executemany(insert_query, data)

    connection.commit()

    print("\nCleaned Data Loaded into MySQL Successfully!")



    cursor.execute("SELECT * FROM cleaned_sales")

    result = cursor.fetchall()

    print("\nFinal Data in MySQL:")

    for row in result:
        print(row)

    print("\nETL PIPELINE COMPLETED SUCCESSFULLY!")

except mysql.connector.Error as error:
    print("MySQL Error:", error)

except Exception as error:
    print("Error:", error)

finally:
    if 'connection' in locals() and connection.is_connected():
        cursor.close()
        connection.close()
        print("\nMySQL Connection Closed.")
