# from app.database.supabase_client import supabase

# # Fetch all summaries
# response = supabase.table("summaries").select("*").execute()
# print(response.data)
from app.database.supabase_client import supabase

# ⚠️ This will delete ALL rows from "summaries" table
response = supabase.table("summaries").delete().neq("id", 0).execute()

print("All summaries deleted:", response.data)
