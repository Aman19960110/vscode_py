import asyncio
import pandas as pd
from playwright.async_api import async_playwright
import nest_asyncio
import re
import random
import time

# Apply the nest_asyncio patch
nest_asyncio.apply()

# Load the Excel file into a DataFrame
df = pd.read_excel(r"C:\Users\amany\Downloads\atm (3).xlsx")
df['Margin'] = None  # Initialize the Margin column

async def run():
    async with async_playwright() as p:
        # Launch headless browser
        browser = await p.chromium.launch(headless=False)
        
        for index, row in df.iterrows():
            stock = row['stocks']
            atm_strike = row['atm']
            
            print(f"Calculating margin for {stock} with ATM strike price {atm_strike}...")
            
            try:
                # Open a new page for each iteration
                page = await browser.new_page()
                
                # Set a realistic user agent
                await page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
                })
                
                # Go to the Zerodha Margin Calculator URL
                await page.goto('https://zerodha.com/margin-calculator/SPAN/')
                
                # Wait for the page to load completely
                await page.wait_for_load_state('networkidle')
                
                # Random delay before starting interaction (1-3 seconds)
                await page.wait_for_timeout(random.randint(1000, 3000))
                
                # Open the dropdown for selecting the symbol
                await page.click('span#select2-scrip-container')
                await page.wait_for_selector('ul.select2-results__options')
                
                # Search for the stock with expiry date
                search_input = await page.query_selector('.select2-search__field')
                
                # Type the text with random delays between characters to mimic human typing
                for char in f"{stock} 27-MAR-2025":
                    await search_input.type(char, delay=random.randint(50, 150))
                
                await page.wait_for_timeout(random.randint(800, 1500))
                
                # Check if the stock with this expiry exists in the dropdown
                selector = f'li.select2-results__option:has-text("{stock} 27-MAR-2025")'
                has_stock = await page.query_selector(selector)
                
                if has_stock:
                    await page.click(selector)
                else:
                    print(f"Stock {stock} with expiry 27-MAR-2025 not found, trying alternative format...")
                    # Try alternative formats or dates if needed
                    continue
                
                # Random delay (0.5-1.5 seconds)
                await page.wait_for_timeout(random.randint(500, 1500))
                
                # Select the "SELL" radio button
                await page.click('input[type="radio"][value="sell"]')
                
                # Random delay (0.3-1 seconds)
                await page.wait_for_timeout(random.randint(300, 1000))
                
                # Click the "Add" button
                await page.click('input[type="submit"][value="Add"]')
                
                # Wait for the form to update with random delay (1-2 seconds)
                await page.wait_for_timeout(random.randint(1000, 2000))
                
                # Select "Options" from the product dropdown
                await page.wait_for_selector('select#product', state='visible')
                await page.select_option('select#product', value='OPT')
                
                # Random delay (0.3-0.8 seconds)
                await page.wait_for_timeout(random.randint(300, 800))
                
                # Select "Puts" from the option type dropdown
                await page.wait_for_selector('select#option_type', state='visible')
                await page.select_option('select#option_type', value='PE')
                
                # Random delay (0.3-0.8 seconds)
                await page.wait_for_timeout(random.randint(300, 800))
                
                # Enter the ATM strike price
                await page.wait_for_selector('input#strike_price', state='visible')
                # Clear the field first
                await page.fill('input#strike_price', '')
                # Type the strike price with random delays
                for char in str(atm_strike):
                    await page.type('input#strike_price', char, delay=random.randint(50, 150))
                
                # Random delay (0.5-1 seconds)
                await page.wait_for_timeout(random.randint(500, 1000))
                
                # Click the "Add" button
                await page.click('input[type="submit"][value="Add"]')
                
                # Wait for the form to update with random delay (1-2 seconds)
                await page.wait_for_timeout(random.randint(1000, 2000))
                
                # Select "Calls" from the option type dropdown
                await page.wait_for_selector('select#option_type', state='visible')
                await page.select_option('select#option_type', value='CE')
                
                # Random delay (0.3-0.8 seconds)
                await page.wait_for_timeout(random.randint(300, 800))
                
                # Select the "BUY" radio button
                await page.click('input[type="radio"][value="buy"]')
                
                # Random delay (0.5-1 seconds)
                await page.wait_for_timeout(random.randint(500, 1000))
                
                # Click the "Add" button
                await page.click('input[type="submit"][value="Add"]')
                
                # Wait longer for the page to update the margin value with random delay (2-4 seconds)
                await page.wait_for_timeout(random.randint(2000, 4000))
                
                # Try different selectors for total margin
                total_margin = None
                selectors = [
                    'span.val.total', 
                    '.margin-calculator-wrap .total', 
                    '.total-row .total-value',
                    '.grand-total-row .value',
                    'span.total:not(.label)'
                ]
                
                for selector in selectors:
                    try:
                        element = await page.wait_for_selector(selector, timeout=1000)
                        if element:
                            total_margin = await element.inner_text()
                            # Clean up the margin value (remove ₹, commas, etc.)
                            if total_margin:
                                total_margin = re.sub(r'[^\d.]', '', total_margin)
                                break
                    except:
                        continue
                
                if total_margin:
                    print(f"Total Margin for {stock}: {total_margin}")
                    df.at[index, 'Margin'] = total_margin
                else:
                    print(f"Could not extract margin for {stock}")
                    
                # Take a screenshot for debugging
                #await page.screenshot(path=f"{stock}_margin.png")
                
            except Exception as e:
                print(f"Error processing {stock}: {str(e)}")
            
            finally:
                # Close the page
                if 'page' in locals() and page:
                    await page.close()
                
                # Add a longer delay between stocks (5-15 seconds) to avoid detection
                delay_seconds = random.uniform(1, 6)
                print(f"Waiting {delay_seconds:.2f} seconds before processing next stock...")
                await asyncio.sleep(delay_seconds)
        
        # Close the browser after processing all stocks
        await browser.close()

# Run the async function
# Replace the direct await call
# await run()

# With this instead:
if __name__ == "__main__":
    asyncio.run(run())

# Print the updated DataFrame with margin values
print("\nUpdated DataFrame with Margin values:")
print(df)

# Save the updated DataFrame back to Excel
df.to_excel("//content/atm_with_margins.xlsx", index=False)