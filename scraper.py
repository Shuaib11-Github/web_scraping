import requests  # Import the requests library to handle HTTP requests
from bs4 import BeautifulSoup  # Import BeautifulSoup for parsing HTML
import pandas as pd  # Import pandas for data manipulation and saving the data to CSV
import numpy as np  # Import numpy for handling missing values (NaN)
import re  # Import the regular expression library for cleaning text

# Function to extract the product title from the product page
def get_title(soup):
    try:
        # Attempt to find the title element in the HTML using the ID 'productTitle'
        title = soup.find("span", attrs={"id": 'productTitle'}).text.strip()
    except AttributeError:
        # If the title is not found, return a default message
        title = "Title not found"
    return title

# Function to extract the product price from the product page
def get_price(soup):
    try:
        # Attempt to find the regular price (if available) by ID 'priceblock_ourprice'
        price = soup.find("span", attrs={'id': 'priceblock_ourprice'}).text.strip()
    except AttributeError:
        try:
            # If the regular price is not found, try to find a sale or deal price
            price = soup.find("span", attrs={'id': 'priceblock_dealprice'}).text.strip()
        except AttributeError:
            try:
                # If both previous prices are not found, attempt to find the sale price
                price = soup.find("span", attrs={'id': 'priceblock_saleprice'}).text.strip()
            except AttributeError:
                try:
                    # If no price is found, attempt to extract the whole and fraction parts separately
                    whole_price = soup.find("span", {"class": "a-price-whole"}).text.strip()
                    fraction_price = soup.find("span", {"class": "a-price-fraction"}).text.strip()
                    
                    # Combine whole and fraction parts to form the full price
                    price = f"{whole_price}.{fraction_price}"
                    
                    # Clean up the price by removing any non-numeric characters
                    price = re.sub(r'[^\d.]', '', price)  # Keep only numbers and the decimal point
                    # Ensure there's only one decimal point
                    price = price if price.count('.') <= 1 else price.replace('.', '', price.count('.') - 1)

                except AttributeError:
                    # If no price could be found, return a default message
                    price = "Price not found"
    return price

# Function to extract the product rating from the product page
def get_rating(soup):
    try:
        # Attempt to find the rating element using the class 'a-icon-alt'
        rating = soup.find("span", attrs={'class': 'a-icon-alt'}).text.strip()
    except AttributeError:
        # If the rating is not found, return a default message
        rating = "Rating not found"
    return rating

# Function to extract the seller's name from the product page
def get_seller_name(soup):
    try:
        # Attempt to find the seller's name using the ID 'sellerProfileTriggerId'
        seller = soup.find("a", attrs={'id': 'sellerProfileTriggerId'}).text.strip()
    except AttributeError:
        # If the seller name is not found, return a default message
        seller = "Unknown Seller"
    return seller

# Function to fetch product data from a given URL
def fetch_product_data(url, headers):
    try:
        # Send a GET request to the product URL with the specified headers
        response = requests.get(url, headers=headers)
        # Raise an exception if the request was not successful
        response.raise_for_status()
        # Parse the HTML content of the page
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract the product details by calling the respective functions
        title = get_title(soup)
        price = get_price(soup)
        rating = get_rating(soup)
        seller = get_seller_name(soup)

        # Return the extracted data as a dictionary
        return {
            "Product Name": title,
            "Price": price,
            "Rating": rating,
            "Seller Name": seller
        }
    except requests.exceptions.RequestException as e:
        # If an error occurs during the request, print the error and return None
        print(f"Error fetching {url}: {e}")
        return None

# Main block of code to execute the scraping process
if __name__ == '__main__':
    # Define headers with a user agent to mimic a real browser request (to avoid blocking)
    HEADERS = ({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Safari/537.36',
        'Accept-Language': 'en-US, en;q=0.5'
    })

    # Define the URL for the search page (products to scrape)
    search_url = "https://www.amazon.in/s?rh=n%3A6612025031&fs=true&ref=lp_6612025031_sar"
    # Fetch the search page content
    search_page = requests.get(search_url, headers=HEADERS)
    # Parse the HTML content of the search page
    soup = BeautifulSoup(search_page.content, "html.parser")

    # Create a set to store product links (using a set avoids duplicates)
    product_links = set()
    # Extract all product links from the search page
    for link_tag in soup.find_all("a", class_='a-link-normal s-no-outline'):
        link = link_tag.get('href')
        # Ensure the link is a product link (contains '/dp/')
        if link and "/dp/" in link:
            # Add the full product URL to the set
            full_link = "https://www.amazon.in" + link
            product_links.add(full_link)

    # Create an empty dictionary to store the data for each product
    data = {"Product Name": [], "Price": [], "Rating": [], "Seller Name": []}

    # Loop through each product link and fetch the product data
    for link in product_links:
        product_data = fetch_product_data(link, HEADERS)
        if product_data:
            # If product data is successfully fetched, append it to the data dictionary
            data['Product Name'].append(product_data['Product Name'])
            data['Price'].append(product_data['Price'])
            data['Rating'].append(product_data['Rating'])
            data['Seller Name'].append(product_data['Seller Name'])

    # Convert the collected data into a pandas DataFrame
    amazon_df = pd.DataFrame(data)
    # Replace any empty strings with NaN values
    amazon_df.replace("", np.nan, inplace=True)
    # Drop any rows with missing product names (since we can't use incomplete data)
    amazon_df.dropna(subset=['Product Name'], inplace=True)
    # Save the data to a CSV file
    amazon_df.to_csv("amazon_data.csv", index=False, header=True)
    print("Data saved to amazon_data.csv")