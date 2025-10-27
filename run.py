# import uvicorn

# if __name__ == "__main__":
#     uvicorn.run(
#         "app.main:app",
#         host="0.0.0.0",
#         port=8000,
#         reload=True
#     )
import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Render sets the PORT env variable
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",  # bind to all interfaces
        port=port,
        reload=False      # disable auto-reload in production
    )
