import pytest
from fte_scraper import get_html, parse_thread_page, parse_forum_page, save_to_db

# Mocked HTML content for testing
mock_thread_html = """
<html>
<head><title>Test Thread</title></head>
<body>
    <div id="post_message_1">Question content</div>
    <div id="post_message_2">Response content 1</div>
    <div id="post_message_3">Response content 2</div>
</body>
</html>
"""

mock_forum_html = """
<html>
<head><title>Test Forum</title></head>
<body>
    <a href="thread1.html">Thread 1</a>
    <a href="thread2.html">Thread 2</a>
</body>
</html>
"""

def test_get_html(monkeypatch):
    def mock_get(*args, **kwargs):
        class MockResponse:
            def __init__(self, text, status_code):
                self.text = text
                self.status_code = status_code
        return MockResponse("<html></html>", 200)
    
    monkeypatch.setattr("requests.get", mock_get)
    html = get_html("http://example.com")
    assert html == "<html></html>"
    print("test_get_html passed")

def test_parse_thread_page():
    question, responses = parse_thread_page(mock_thread_html)
    assert question == "Question content"
    assert responses == ["Response content 1", "Response content 2"]
    print("test_parse_thread_page passed")

def test_parse_forum_page():
    thread_urls = parse_forum_page(mock_forum_html)
    assert thread_urls == ["thread1.html", "thread2.html"]
    print("test_parse_forum_page passed")

# To test `save_to_db`, we need to use a temporary SQLite database
import sqlite3

def test_save_to_db(tmp_path):
    db_file = tmp_path / "test.db"
    conn = sqlite3.connect(db_file)
    conn.execute("CREATE TABLE IF NOT EXISTS forum_data (question TEXT, response TEXT)")
    conn.commit()

    save_to_db("Question?", ["Response 1", "Response 2"])

    cursor = conn.execute("SELECT question, response FROM forum_data")
    data = cursor.fetchall()

    assert len(data) == 2
    assert data[0] == ("Question?", "Response 1")
    assert data[1] == ("Question?", "Response 2")

    conn.close()
    print("test_save_to_db passed")

if __name__ == '__main__':
    pytest.main(["-v", "--tb=line", "-rN", __file__])
    
