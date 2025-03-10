import asyncio
import pandas as pd
from playwright.async_api import async_playwright

# Create a DataFrame
df = pd.read_excel("C:\\Users\\amany\\Downloads\\atm.xlsx")

# Define the async function to interact with Zerodha Margin Calculator
async def run():
    async with async_playwright() as p:
        # Launch headless browser
        browser = await p.chromium.launch(headless=False,slow_mo=1000)

        # Open a new page
        page = await browser.new_page()

        # Go to the Zerodha Margin Calculator URL
        await page.goto('https://zerodha.com/margin-calculator/SPAN/')

        # Wait for the page to load completely
        await page.wait_for_load_state('load')

        # Loop through each row in the DataFrame
        for index, row in df.iterrows():
            stock = row['stocks']
            atm_strike = row['atm']

            print(f"Calculating margin for {stock} with ATM strike price {atm_strike}...")

            # Open the dropdown for selecting the symbol (e.g., Reliance)
            await page.click('span#select2-scrip-container')
            await page.wait_for_selector('ul.select2-results__options')

            # Select the stock symbol from the dropdown
            await page.click(f'li.select2-results__option:has-text("{stock} 26-DEC-2024")')

            # Select the "SELL" radio button
            await page.click('input[type="radio"][value="sell"]')

            # Click the "Add" button
            await page.click('input[type="submit"][value="Add"]')

            # Select "Options" from the product dropdown
            await page.wait_for_selector('select#product', state='visible')
            await page.select_option('select#product', value='OPT')  # Select "Options"

            # Wait for the "option_type" dropdown to be visible and select "Puts" (value="PE")
            await page.wait_for_selector('select#option_type', state='visible')
            await page.select_option('select#option_type', value='PE')  # Select "Puts" option

            # Enter the ATM strike price into the strike price input field
            await page.wait_for_selector('input#strike_price', state='visible')
            await page.fill('input#strike_price', str(atm_strike))  # Enter ATM strike price

            # Click the "Add" button
            await page.click('input[type="submit"][value="Add"]')

            # Wait for the "option_type" dropdown to be visible and select "Puts" (value="CE")
            await page.wait_for_selector('select#option_type', state='visible')
            await page.select_option('select#option_type', value='CE')  # Select "Call" option

            # Select the "SELL" radio button
            await page.click('input[type="radio"][value="buy"]')

             # Click the "Add" button
            await page.click('input[type="submit"][value="Add"]')

            # Wait for a few seconds to let the page update the margin value
            await page.wait_for_timeout(3000)

            # Wait for the Total Margin value to appear and extract it
            await page.wait_for_selector('span.val.total', timeout=5000)
            total_margin = await page.inner_text('span.val.total')

            # Print the Total Margin value
            print(f"Total Margin for {stock}: {total_margin}")

            # Update the margin value in the DataFrame
            df.at[index, 'Margin'] = total_margin

            # Click the "Reset" button to clear the form for the next stock calculation
            await page.click('input#reset')  # Click the Reset button to clear the form

            # Wait for the page to reset (optional)
            await page.wait_for_load_state('load')

        # Close the browser
        await browser.close()

# Entry point for the script
if __name__ == "__main__":
    asyncio.run(run())

    # Print the updated DataFrame with margin values
    print("\nUpdated DataFrame with Margin values:")
    print(df)
    
