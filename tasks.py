from robocorp.tasks import task
from robocorp import browser
from RPA.HTTP import HTTP
from RPA.Tables import Tables
from RPA.PDF import PDF
import os
from shutil import make_archive

@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """
    open_robot_order_website("https://robotsparebinindustries.com/#/robot-order")
    orders = get_orders()
    process_orders(orders)
    archive_receipts()



def open_robot_order_website(url):
    browser.configure(slowmo=100)
    browser.goto(url)

def close_annoying_modal():
    page=browser.page()
    modal = page.locator("div[class='modal-content']").count()
    print(str(modal))
    if modal >= 1:
        page.click("//button[text()='OK']")

def get_orders():
    http=HTTP()
    http.download(url="https://robotsparebinindustries.com/orders.csv", overwrite=True)
    table=Tables()
    orders=table.read_table_from_csv("orders.csv",header=True)
    return orders

def process_orders(orders):
    page=browser.page()
    """fill on all the orders and submit.
    Store receipt as pdf and make a screenshot of robot.
    store receipt and screenshot in one pdf file"""
    for order in orders:
        close_annoying_modal()
        fill_the_form(order)
        submit_order()
        pdf_file = store_receipt_as_pdf(order['Order number'])
        screenshot = screenshot_robot(order['Order number'])
        embed_screenshot_to_receipt(screenshot, pdf_file)
        """order another robot"""
        page.click("button[id='order-another']")

def fill_the_form(order):
    page=browser.page()
    """fill in one order and click preview"""
    page.fill("input[id='address']",order['Address'])
    page.select_option("select[id='head']",order['Head'])
    page.click("input[id='id-body-{}']".format(order['Body']))
    page.fill("input[placeholder='Enter the part number for the legs']",order['Legs'])
    
    page.click("button[id='preview']")


def submit_order():
    page=browser.page()
    """submit order. If the error comes up, click submit order once again"""
    page.click("button[id='order']")

    alert_count = page.locator("div[class='alert alert-danger']").count()
    while alert_count >=1:
        page.click("button[id='order']")
        alert_count = page.locator("div[class='alert alert-danger']").count()

def store_receipt_as_pdf(order_number):
    pdf=PDF()
    page=browser.page()
    receipts_dir = "output/receipts"
    os.makedirs(receipts_dir, exist_ok=True)
    receipt = page.locator("div[id='receipt']").inner_html()
    receipts_path = "output/receipts/{}.pdf".format(order_number)
    pdf.html_to_pdf(receipt, receipts_path)
    return receipts_path

def screenshot_robot(order_number):
    page=browser.page()
    screenshots_dir = "output/screenshots"
    os.makedirs(screenshots_dir, exist_ok=True)
    robot_img = page.locator("div[id='robot-preview-image']")
    screenshot_path = "output/screenshots/{}.png".format(order_number)
    robot_img.screenshot(path = screenshot_path)
    return screenshot_path

def embed_screenshot_to_receipt(screenshot, pdf_file):
    pdf=PDF()
    list_of_files = [pdf_file, screenshot]
    pdf.add_files_to_pdf(files= list_of_files, target_document = pdf_file, append = False)

def archive_receipts():
    make_archive("output/receipts_archived","zip","output/receipts")
