newstastic
==========

License
-------
This work licensed under a [Creative Commons Attribution-ShareAlike 3.0 Unported License](http://creativecommons.org/licenses/by-sa/3.0/).

I do not own the template provided with this module, it was taken from [mailchimp/email-blueprints](http://github.com/mailchimp/email-blueprints) and modified, as allowed by the [Creative Commons Attribution-ShareAlike 3.0 Unported License](http://creativecommons.org/licenses/by-sa/3.0/).

Usage Instructions
------------------
1. Modify template.html, adding your image, footer, and title. Do not replace magic strings (e.g. **\*|TEASER\*|**).
   Optionally, modify the CSS to make your own custom style.

2. Create an XML file following the example.xml. Any HTML embedded within the XML doc should be escaped.

3. Execute ````python send_email.py xml/your_xml_doc.xml````
