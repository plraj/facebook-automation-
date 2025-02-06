import random
import time
import os
import google.generativeai as genai
from playwright.sync_api import sync_playwright
import requests
import base64
import profile_checker

# ✅ Initialize Gemini API

genai.configure(api_key = API_KEY)

# ✅ Create folder for images
os.makedirs("facebook_images", exist_ok=True)

# ✅ Load Image from URL and Save Locally
def download_and_save_image(image_url, index):
    try:
        response = requests.get(image_url)
        if response.status_code == 200:
            # Save the image locally
            image_path = f"facebook_images/post_{index}.jpg"
            with open(image_path, "wb") as file:
                file.write(response.content)
            print(f"📥 Image saved: {image_path}")
            # Convert the image to base64 for Gemini API usage
            image_bytes = base64.b64encode(response.content).decode('utf-8')
            return image_bytes, image_path
        else:
            print(" Failed to download the image.")
            return None, None
    except Exception as e:
        print(f"⚠️ Error downloading image: {e}")
        return None, None

# ✅ Generate AI Comment Using Gemini API
def generate_image_comment(image_bytes, about_image , comment_text):
    if image_bytes is None:
        return "Error loading image for analysis."
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            contents=[
                {"parts": [
                    {"inline_data": {"mime_type": "image/jpeg", "data": image_bytes}},
                    # {"text": f"Generate a critical and good comment for this image focusing on flaws. Keep it critical and respond in Hindi. About section: {about_image} in just 10 word"},
                    {"text": f"here is About this pic: {about_image} , {comment_text} . respond in Hindi in just 10 word."}
                ]}
            ]
        )
        return response.text.strip()
    except Exception as e:
        print(f"⚠️ Error generating comment: {e}")
        return "Nice"


def process_profile_and_generate_comment(post, profile_checker, generate_image_comment, image_bytes, about_section):
    try:
        # Locate the profile name div and extract the anchor tag's href
        profile_name_div = post.locator('[data-ad-rendering-role="profile_name"]')
        anchor_tag = profile_name_div.locator('a').first  # Select the first matching anchor tag

        href_value = anchor_tag.get_attribute('href')

        if href_value:
            # Process the link to remove everything after "?" symbol
            clean_link = href_value.split('?')[0]
            print(f"Extracted link before '?' - profile url: {clean_link}")

            # Check if the profile is good, bad, or not in the list
            result = profile_checker.is_good_account(clean_link)
            print(f"Profile Check Result: {result}")

            # Define comment text based on the profile type
            if result == True:
                comment_text = "generate a very good comment about this post."
            elif result == False:
                comment_text = "Generate a bad comment about this photo"
            elif result == "not in list":
                comment_text = "Generate a good comment about this photo"

            # Generate the AI-powered comment

            ai_generated_comment = generate_image_comment(image_bytes, about_section, comment_text)
            return ai_generated_comment
        else:
            print("⚠️ No href attribute found in the <a> tag.")
            return None

    except Exception as e:
        print(f"⚠️ Error extracting link: {e}")
        return None


# ✅ Facebook Automation with Playwright
def facebook_automation(email, password):
    with sync_playwright() as p:

        browser = p.chromium.launch(headless=False)

        # ✅ Check if session file exists
        session_file = "facebook_session.json"
        if os.path.exists(session_file):
            context = browser.new_context(storage_state=session_file)
            print("✅ Using existing session...")
        else:
            context = browser.new_context()
            print("🔐 No session found. Logging in manually.")

        page = context.new_page()

        # ✅ Check for Existing Login Session
        page.goto("https://www.facebook.com/")
        if page.locator("#email").is_visible():
            print("Logging into Facebook...")
            page.fill("#email", email)
            time.sleep(2)
            page.fill("#pass", password)
            time.sleep(2)
            page.click("button[name='login']")
            page.wait_for_timeout(5000)
            context.storage_state(path="facebook_session.json")
        else:
            print("✅ Already Logged In!")

        # do small check
        page.wait_for_timeout(2000)

        if(page.locator('[aria-label="Leave a comment"]')):
            print("yes")
        else:
            print("no")
        
        # ✅ Go to the Home Feed
        # Loop through posts by incrementing aria-posinset
        for i in range(1, 5):  # First 10 posts
            try:

                #✅ Random Scrolling Simulation
                page.mouse.wheel(0, random.randint(300, 900))
                time.sleep(random.uniform(3, 6))

                # Locate the post using aria-posinset
                post = page.locator(f'[aria-posinset="{i}"]')
                if not post:
                    print(f"Post with aria-posinset={i} not found.")
                    continue

                print(f"Processing post {i , post}")

                # Fetch about content of images from post
                try:
                    about_section = post.locator('div[dir="auto"]').first.inner_text()
                    print(f"About section for post {i}: {about_section}")
                except:
                    about_section = "No about section provided."
                    print(f"⚠️ About section missing for post {i}")



                # ✅ Fetch Image URL, Download & Save It
                try:
                    
                    images = post.locator('img').all()
                    
                    fbpost_img_url = None  # To store the URL of the image containing "lion"

                    for image_element in images:
                        image_url = image_element.get_attribute("src")
                        if image_url and "https://scontent" in image_url:
                            fbpost_img_url = image_url
                            break  # Exit the loop once the desired image is found

                    if fbpost_img_url:
                        print(f"Found image with 'scontent' in src: {fbpost_img_url}")
                        image_bytes, image_path = download_and_save_image(fbpost_img_url, i)
                    else:
                        print(f"⚠️ No Image Found with 'scontent' in the src for this post {i}.")
                        image_bytes, image_path = None, None

                except Exception as e:
                    print(f"⚠️ Error fetching images for post {i}: {e}")


                #react or comment on post through feed display 
                action = random.choice(["comment", "react"])

                if action =="comment":
                    try:
                        # Locate comment button
                        comment_box = post.locator('[aria-label="Leave a comment"]')
                        comment_box.click()
                        time.sleep(1)

                        # Check if the comment box is visible
                        fillcmt = post.locator('[aria-label="Write a comment…"]')
                        if fillcmt.count() > 0:
                            print("m")
                            fillcmt.fill("nice post")
                            time.sleep(1)
                            page.keyboard.press("Enter")
                            time.sleep(1)
                            post.locator('[aria-label="Close"]').click()
                            time.sleep(1)

                        elif page.locator('[aria-placeholder="Write a comment…"][role="textbox"]'):
                            print("f")
                            fillcmt = page.locator('[aria-placeholder="Write a comment…"][role="textbox"]')

                            try: 
                                # ✅ Generate AI Comment (with saved image)
                                print("ai genrated comment start")
                                
                                analysis_profile_and_generated_comment = process_profile_and_generate_comment(
                                    post, profile_checker, generate_image_comment, image_bytes, about_section
                                )
                                
                                # ai_generated_comment = generate_image_comment(image_bytes, about_section)
                                # time.sleep(1)
                                print(analysis_profile_and_generated_comment)
                                fillcmt.fill(analysis_profile_and_generated_comment)
                                time.sleep(1)
                                page.keyboard.press("Enter")
                                try:
                                    close_button = page.locator('[role="dialog"] [aria-label="Close"]')
                                    close_button.click()
                                    print("✅ Post closed successfully.")
                                except Exception as e:
                                    print(f"⚠️ Error closing the post: {e}")
                                    page.keyboard.press("Escape")
                            except:
                                fillcmt.fill("nice ")
                                print("not able to gernate comment through gemini")

                            # time.sleep(1)
                            # page.keyboard.press("Enter")
                            # time.sleep(1)
                            # page.locator('[aria-label="Close"]').click()
                            time.sleep(1)
                        else:
                            print(f"comment box open but not able to write comment on post {i}")
                    except:
                        print(f"comment box not found for post {i}: {e}")

                elif action == "react":

                    try:
                        like_button = post.locator('[aria-label="Like"]')
                        if like_button.count() > 0:
                            like_button.first.click()
                            print(f"👍 Reacted to post {i}")
                        else:
                            print(f"No Like button found for post {i}")
                    except Exception as e:
                        print(f"Error interacting with Like button for post {i}: {e}")

            except Exception as e:
                print(f"⚠️ Error processing post {i}")

        print("🎯 Task Completed!")
        browser.close()



