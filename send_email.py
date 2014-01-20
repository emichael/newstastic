# This script sends an email to the a List Serve based on an XML document
# describing that email.
#
# This script depends on premailer.
# https://pypi.python.org/pypi/premailer

__author__ = 'Ellis Michael (ellis@ellismichael.com)'


from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import getpass
import os
import premailer
import re
import smtplib
import sys
import time
import textwrap
from xml.dom import minidom
import webbrowser


SERVER_EMAIL_FOLDER = 'http://notarealdomainname.null'
LIST_SERVE_EMAIL = 'fakelist@listserves.null'
ORGANIZATION_NAME = 'My Organization'
NEWSLETTER_TITLE = 'Our Weekly News'

TEMPLATE_FILE_NAME = 'template.html'

EDITOR_MAGIC_STRING = '*|EDITOR|*'
SUBJECT_MAGIC_STRING = '*|SUBJECT|*'
DATE_MAGIC_STRING = '*|DATE|*'
TEASER_MAGIC_STRING = '*|TEASER|*'
SERVER_URL_MAGIC_STRING = '*|HTMLFILE|*'
BEGIN_MAIN_CONTENT_MAGIC_STRING = '<!-- *|BEGIN_CONTENT|* -->'
END_MAIN_CONTENT_MAGIC_STRING = '<!-- *|END_CONTENT|* -->'
BEGIN_SIDEBAR_MAGIC_STRING = '<!-- *|BEGIN_SIDEBAR|* -->'
END_SIDEBAR_MAGIC_STRING = '<!-- *|END_SIDEBAR|* -->'

SMTP_SERVER = 'smtp.gmail.com:587'


def get_email_data(xml_doc):
  ## Grab data from file ##
  email_data = {}
  email_data['date'] = str(xml_doc.getAttribute('date'))
  email_data['editor'] = str(xml_doc.getAttribute('editor'))
  email_data['volume'] = str(xml_doc.getAttribute('volume'))
  email_data['issue'] = str(xml_doc.getAttribute('issue'))

  def add_item_child_to_dict(xml_item, item_dict, child_node_name):
    if xml_item.getElementsByTagName(child_node_name):
      item_dict[child_node_name] = str(
        xml_item.getElementsByTagName(child_node_name)[0].firstChild.nodeValue)

  add_item_child_to_dict(xml_doc, email_data, 'teaser')

  # Now process items
  items = []
  categories = []
  for xml_item in xml_doc.getElementsByTagName(
      'itemList')[0].getElementsByTagName('item'):
    item = {}
    item['name'] = str(xml_item.getAttribute('name'))
    item['category'] = str(xml_item.getAttribute('category'))
    if not item['category'] in categories:
      categories.append(item['category'])
    if xml_item.hasAttribute('type'):
      item['type'] = str(xml_item.getAttribute('type'))
    add_item_child_to_dict(xml_item, item, 'info')
    add_item_child_to_dict(xml_item, item, 'date')
    add_item_child_to_dict(xml_item, item, 'location')
    items.append(item) # append to our list of items

  email_data['items'] = items
  email_data['categories'] = categories
  return email_data


def generate_email_from_data(file_name, email_data):
  ## Open template ##
  template_file = file(TEMPLATE_FILE_NAME)
  output = str(template_file.read())
  template_file.close()

  ## Replace variables ##
  output = output.replace(EDITOR_MAGIC_STRING, email_data['editor'])
  output = output.replace(SUBJECT_MAGIC_STRING,
                          '%s: %s' % (NEWSLETTER_TITLE, email_data['date']))
  output = output.replace(DATE_MAGIC_STRING, email_data['date'])
  output = output.replace(TEASER_MAGIC_STRING, email_data['teaser'])
  output = output.replace(SERVER_URL_MAGIC_STRING,
                          os.path.join(SERVER_EMAIL_FOLDER, file_name))

  ## Now for the main content ##
  content = ""
  for cat in email_data['categories']:
    content += '<h2 class="h2">%s</h2><ol class="itemList">' % cat
    for item in email_data['items']:
      if item['category'] == cat:

        # Get the class of the item
        if 'type' in item:
          if item['type'] == 'urgent':
            item_class = 'urgentItem'
          elif item['type'] == 'new':
            item_class = 'newItem'
        else:
          item_class = 'item'

        # build item
        content += '<li class="%s"><h3 class="title">%s</h3>' % (
          item_class, item['name'])

        # try to add date and location
        try:
          content += '<p class="date">' + item['date']
          try:
            content += ', ' + item['location']
          except KeyError:
            pass
          content += '</p>'
        except KeyError:
          try:
            content += '<p class="date">%s</p>' % item['location']
          except KeyError:
            pass

        content += '<p class="info">%s</p></li>' % item['info']
    content = content + '</ol>'

  # replace main content
  output = (output[:output.index(BEGIN_MAIN_CONTENT_MAGIC_STRING) + 26] +
            content +
            output[output.index(END_MAIN_CONTENT_MAGIC_STRING):])

  ## Now for the sidebar ##
  content = ''
  for cat in email_data['categories']:
    content += '<strong>%s</strong><ol class="itemList">' % cat
    for item in email_data['items']:
      # if item is in this category
      if item['category'] == cat:
        # Get the class of the item
        if 'type' in item:
          if item['type'] == 'urgent':
            item_class = 'urgentItem'
          elif item['type'] == 'new':
            item_class = 'newItem'
        else:
          item_class = 'item'
        # build item
        content = content + '<li class="%s"><p class="title">%s</p>' % (
          item_class, item['name'])
        # date
        if 'date' in item:
          content += '<p class="date">%s</p>' % item['date']
      content += '</li>'
    content += '</ol>'

  # replace sidebar content
  output = (output[:output.index(BEGIN_SIDEBAR_MAGIC_STRING) + 26] +
            content +
            output[output.index(END_SIDEBAR_MAGIC_STRING):])

  return output


def premail_email(email_html):
  processed_html = premailer.transform(email_html)
  return processed_html


def send_email(html_email, volume_no, issue_no):
  senders_name = raw_input('Sender\'s name: ')
  senders_email = raw_input('Sender\'s Gmail Address: ')
  password = getpass.getpass()

  msg = MIMEMultipart('alternative')
  msg['Subject'] = "%s: Volume %s, Issue %s" % (NEWSLETTER_TITLE,
                                                volume_no, issue_no)
  msg['From'] = "%s <%s>" % (senders_name, senders_email)
  msg['To'] = "%s <%s>" % (ORGANIZATION_NAME, LIST_SERVE_EMAIL)

  # Break up lines to prevent SMTP overflow
  seg_html_email = textwrap.fill(html_email, 800)
  part = MIMEText(seg_html_email, 'html')
  msg.attach(part)

  try:
    server = smtplib.SMTP(SMTP_SERVER)
    server.starttls()
    server.login(senders_email, password)
    server.sendmail(senders_email, LIST_SERVE_EMAIL, msg.as_string())
  finally:
    server.quit()


def main(argv=sys.argv):
  # Load xml document
  xml_file_name = argv[1]
  print ('Loading: %s' % xml_file_name)
  xml_file = file(xml_file_name)
  xml_doc = minidom.parseString(
    xml_file.read()).getElementsByTagName('weeklyEmail')[0]
  xml_file.close()

  # Process email data
  print('Generating email html.')
  email_data = get_email_data(xml_doc)
  html_file_name = os.path.basename(xml_file_name).replace('.xml', '.html')
  output = generate_email_from_data(html_file_name, email_data)
  output = premail_email(output)
  output = re.sub(r'[ \t\r\n]+', ' ', output) # Strip whitespace

  # Handle output
  print('Writing email to file: %s' % html_file_name)
  output_file = file(html_file_name, 'w')
  output_file.write(output)
  output_file.close()
  # Open email in browser, confirm sending
  print('Opening the email file for review.\n'
        'Check that it is correct and upload it to %s before continuing!\n' %
        SERVER_EMAIL_FOLDER)
  time.sleep(1)
  output_filepath = os.path.join(os.getcwd(), html_file_name)
  savout = os.dup(1)
  os.close(1)
  os.open(os.devnull, os.O_RDWR)
  try:
     webbrowser.open('file://' + output_filepath)
  finally:
     os.dup2(savout, 1)
  confirmation = raw_input('Would you like to send the email? (y/n) ')
  if confirmation in ['y', 'Y']:
    try:
      send_email(output, email_data['volume'], email_data['issue'])
      print('Email sent.')
    except smtplib.SMTPAuthenticationError as e:
      print e[1]
      print('Sending failed.')

if __name__ == '__main__':
  main()
