"""Debug sub-table structure."""
import re
html = open("debug_popup.html", encoding="utf-8").read()
# Find table
idx = html.find("mat-elevation-z2")
if idx >= 0:
    print("TABLE found at", idx)
    # Get the table content
    end = html.find("</table>", idx)
    if end == -1:
        end = idx + 3000
    print(html[idx-200:end+8])
else:
    print("TABLE not found in truncated HTML")
    # The table might be after 10k chars
    print("HTML length:", len(html))
