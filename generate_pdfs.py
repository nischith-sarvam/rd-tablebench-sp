import os
from bs4 import BeautifulSoup
import weasyprint
from pathlib import Path
import glob

def create_pdfs_from_tables(template_path, tables_folder, output_folder, base_font_size=5):
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Load the HTML template
    with open(template_path, 'r', encoding='utf-8') as file:
        template_html = file.read()
    
    # Get all table HTML files
    # table_files = glob.glob(os.path.join(tables_folder, '*.html'))
    table_files = ["/home/vansh/work/sarvam/rd-tablebench-sp/data/groundtruth_sp/19099_png.rf.5168ded02a5cfb7b6d7a90ffe3d405c3.html"]
    
    for i, table_file in enumerate(table_files):
        table_filename = os.path.basename(table_file)
        
        # Load the table HTML
        with open(table_file, 'r', encoding='utf-8') as file:
            table_html = file.read()
        
        # Create soup object from template
        soup = BeautifulSoup(template_html, 'html.parser')
        
        # Find the body tag to append the table
        body_tag = soup.find('body')
        
        # Create a new tag for the table and insert it
        table_soup = BeautifulSoup(table_html, 'html.parser')
        body_tag.append(table_soup)
        
        # Add comprehensive CSS to control layout and prevent overflow
        existing_style = soup.find("style")
        new_style = f"""
            @page {{
                size: A4;
                margin: 10mm;
            }}
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                font-size: {base_font_size}px;
                page-break-inside: avoid;
                table-layout: fixed;
                max-width: 190mm; /* Adjusted for A4 page width */
            }}
            td, th {{
                border: 1px solid #ddd;
                padding: 1.5px;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }}
            @media print {{
                table {{
                    break-inside: avoid;
                }}
            }}
        """

        if existing_style:
            # Append new style instead of overwriting
            existing_style.string += new_style
        else:
            # If no existing <style> tag, create one
            style_tag = soup.new_tag('style')
            style_tag.string = new_style
            soup.head.append(style_tag)
        
        # Generate the new HTML with the table inserted
        final_html = str(soup)
        
        # Temporary HTML file path
        temp_html_path = os.path.join(output_folder, f"temp_{i}.html")
        
        # Write to temporary HTML file
        with open(temp_html_path, 'w', encoding='utf-8') as file:
            file.write(final_html)
        
        # Output PDF path
        pdf_path = os.path.join(output_folder, f"{Path(table_filename).stem}.pdf")
        
        # Configuration for PDF generation
        pdf_options = {
            'enable-local-file-access': None,
            'page-size': 'A4',
            'margin-top': '10mm',
            'margin-right': '10mm',
            'margin-bottom': '10mm', 
            'margin-left': '10mm',
        }
        
        # Generate PDF
        try:
            weasyprint.HTML(filename=temp_html_path).write_pdf(
                pdf_path, 
                # Optional: You can uncomment and adjust these stylesheets if needed
                # stylesheets=[weasyprint.CSS(string=new_style)]
            )
            print(f"Successfully generated PDF: {pdf_path}")
        except Exception as e:
            print(f"Error generating PDF for {pdf_path}: {e}")
        
        # Clean up temporary HTML file
        os.remove(temp_html_path)


        

# Example usage
currPath = os.getcwd()
template_path = os.path.join(currPath, "template.html")  # Your main HTML template
tables_folder = os.path.join(currPath, "data/groundtruth") # Folder containing your table HTML files
output_folder = os.path.join(currPath, "data/pdfs_sp")  # Folder where PDFs will be saved
base_font_size = 8  # Starting font size to try

create_pdfs_from_tables(template_path, tables_folder, output_folder, base_font_size)
