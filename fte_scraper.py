import requests 
from bs4 import BeautifulSoup 
import sqlite3  
import time  

# Base URL of the forum archive page
BASE_URL = 'https://www.ford-trucks.com/forums/archive/index.php/'

# Path to save the database on the removable drive
DB_PATH = '/Volumes/mineral/scraper/forum_data.db'

# Function to get the HTML content of a page
def get_html(url):
    response = requests.get(url)  # Send GET request to the URL
    if response.status_code == 200:  # Check if the request was successful
        print(f"Getting HTML content from: {url}")
        return response.text  # Return the HTML content
    else:
        print(f"Failed to get HTML content from: {url}, Status Code: {response.status_code}")
        return None  # Return None if the request failed

# Function to parse a thread and extract questions and responses
def parse_thread_page(html):
    soup = BeautifulSoup(html, 'html.parser')  # Parse the HTML content with BeautifulSoup
    messages = []  # List to store messages
    
    # Find all elements where the ID contains 'post_message'
    for message in soup.find_all(id=lambda x: x and 'post_message' in x):
        messages.append(message.text.strip())  # Add the text of each message to the list
        print(f"Message: {message.text.strip()}") #debugging
    
    if messages:
        question = messages[0]  # Assume the first message is the question
        responses = messages[1:]  # The rest are responses
    else:
        question = None  # No question found
        responses = []  # No responses found

    return question, responses  # Return the question and responses

# Function to parse the forum page and get thread URLs LOOP IS STUCK HERE-------------------------------------
def parse_forum_page(html):
    soup = BeautifulSoup(html, 'html.parser')  # Parse the HTML content with BeautifulSoup
    # Find all anchor tags and extract their href attributes
    thread_urls = [a['href'] for a in soup.find_all('a') if a.get('href')]
    if len(thread_urls) > 3:
        del thread_urls[:3]
    print(f"Thread URLs: {thread_urls}")
    return thread_urls  # Return the list of thread URLs

# Function to parse the archive page and get category URLs
def parse_archive_page(html):
    soup = BeautifulSoup(html, 'html.parser')  # Parse the HTML content with BeautifulSoup
    # Find all anchor tags within 'li' tags and extract their href attributes
    category_urls = [a['href'] for a in soup.find_all('a') if a.get('href')]
    print(f"Category URLs: {category_urls}")
    if len(category_urls) > 7:
        del category_urls[:7]
    return category_urls  # Return the list of category URLs

# Function to save data into SQLite database
def save_to_db(question, responses):
    conn = sqlite3.connect(DB_PATH)  # Connect to the SQLite database at the specified path
    cursor = conn.cursor()  # Create a cursor object to interact with the database

    # Create 'threads' table if it doesn't exist
    cursor.execute('''CREATE TABLE IF NOT EXISTS threads (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        question TEXT
                    )''')
    
    # Create 'responses' table if it doesn't exist
    cursor.execute('''CREATE TABLE IF NOT EXISTS responses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        thread_id INTEGER,
                        response TEXT,
                        FOREIGN KEY(thread_id) REFERENCES threads(id)
                    )''')

    # Insert data into tables
    cursor.execute('INSERT INTO threads (question) VALUES (?)', (question,))  # Insert question into 'threads' table
    thread_id = cursor.lastrowid  # Get the ID of the last inserted row (thread ID)
    for response in responses:
        cursor.execute('INSERT INTO responses (thread_id, response) VALUES (?, ?)', (thread_id, response))  # Insert each response into 'responses' table

    conn.commit()  # Commit the transaction
    conn.close()  # Close the database connection

# Function to handle pagination within a category
def get_category_pages(base_url):
    page_number = 2  # Start with the first page
    while True:
        url = f"{base_url}-p-{page_number}"  # Construct the URL for the current page
        html = get_html(url)  # Get the HTML content of the page
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            li_elements = soup.find_all('li')
            
            if not li_elements:
                print(f"No <li> elements found on page {page_number}. Stopping pagination.")
                break
            
            print(f"Processing page {page_number} of {base_url}")
            yield html  # Yield the HTML content for processing
            page_number += 1  # Move to the next page
            time.sleep(1)  # Be nice to the server: add a delay between requests
        else:
            print(f"No more pages at {base_url}")
            break  # Stop if no HTML content is returned (end of pages)
         
# Main function to run the scraper
def main():
    archive_html = get_html(BASE_URL)  # Get the HTML content of the archive page
    
    if archive_html is None:  # Check if the HTML content is None
        print("Failed to retrieve the archive page. Exiting.")
        return

    category_urls = parse_archive_page(archive_html)  # Get category URLs from the archive page
    
    # Loop through each category URL
    for category_url in category_urls:
        full_category_url = category_url  # Category URL is already absolute
        print(f"Processing category: {full_category_url}")
        
        # Loop through all pages of the category
        for category_page_html in get_category_pages(full_category_url):
            thread_urls = parse_forum_page(category_page_html)  # Get thread URLs from the current category page
            
            # Loop through each thread URL on the current category page
            for thread_url in thread_urls:
                full_thread_url = thread_url  # Thread URL is already absolute
                print(f"Processing thread: {full_thread_url}")
                thread_html = get_html(full_thread_url)  # Get HTML content of the thread
                if thread_html is not None:  # Check if HTML content is retrieved
                    question, responses = parse_thread_page(thread_html)  # Parse the thread to get question and responses
                    if question:  # Ensure there is a question to save
                        save_to_db(question, responses)  # Save the question and responses to the database
                    time.sleep(1)  # Be nice to the server: add a delay between requests



if __name__ == '__main__':
    main()  # Run the main function
