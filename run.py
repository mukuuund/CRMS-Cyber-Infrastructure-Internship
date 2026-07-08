import uvicorn
import webbrowser
import threading
import time

def open_browser():
    time.sleep(1.5)  # Wait a moment for the server to spin up
    webbrowser.open("http://127.0.0.1:8000/ui/dashboard")

if __name__ == "__main__":
    # Automatically open the browser
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run the FastAPI app using uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
