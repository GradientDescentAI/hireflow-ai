import asyncio
from playwright.async_api import async_playwright
from langchain_google_genai import ChatGoogleGenerativeAI
from core.config import settings
from models.schemas import JobDescription

def generate_linkedin_post(jd: JobDescription) -> str:
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0.7,
        google_api_key=settings.GEMINI_API_KEY
    )
    
    # Must Haves
    mandatory = ", ".join([m.criterion for m in jd.must_haves])
    
    prompt = f"""
    Write a LinkedIn post based on this job description.
    Role: {jd.title} ({jd.location.type})
    Mandatory Requirements: {mandatory}
    
    MUST INCLUDED CALL TO ACTION AT THE END:
    "To apply, email your CV to apply-{jd.id}@hireflow.ai with the subject line: APPLY-{jd.id}"
    
    Max 3000 characters. Professional but engaging tone. Include 8 relevant hashtags.
    """
    
    response = llm.invoke(prompt)
    if hasattr(response, 'content'):
        return response.content
    return str(response)

async def post_to_linkedin(post_content: str):
    """
    Automates the process of logging into LinkedIn and posting.
    Runs non-headless to allow user to resolve MFA / CAPTCHAs manually per PRD spec.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.goto("https://www.linkedin.com/login")
        await page.fill("#username", settings.LINKEDIN_USERNAME)
        await page.fill("#password", settings.LINKEDIN_PASSWORD)
        await page.click("button[type='submit']")
        
        # We wait for up to 60 seconds if MFA is needed for the user to do it
        try:
            # We look for the "Start a post" box as proof of successful login
            await page.wait_for_selector("div.share-box-feed-entry__closed-share-box", timeout=60000)
            await page.click("div.share-box-feed-entry__closed-share-box")
            
            # Wait for text editor box
            await page.wait_for_selector("div.ql-editor")
            await page.fill("div.ql-editor", post_content)
            
            print("Post is ready - User needs to click 'Post' manually for safety during Alpha")
            # await page.click("button.share-actions__primary-action")
            await asyncio.sleep(10) # Wait a bit to observe
            
        except Exception as e:
            print(f"Skipped or failed posting manually: {e}")
        finally:
            await browser.close()
