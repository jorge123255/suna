import io
import json
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from agentpress.tool import Tool, ToolResult, openapi_schema, xml_schema
from sandbox.sandbox import SandboxToolsBase
from agentpress.thread_manager import ThreadManager
from utils.logger import logger

class PDFReportGenerator(SandboxToolsBase):
    """Tool to generate PDF reports from structured data."""
    def __init__(self, project_id: str, thread_manager: ThreadManager):
        super().__init__(project_id, thread_manager)

    @openapi_schema({
        "type": "function",
        "function": {
            "name": "generate_pdf_report",
            "description": "Generate a PDF report from structured data and save it in the sandbox",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title of the PDF report"},
                    "content": {"type": "string", "description": "Content for the report in structured or markdown format"}
                },
                "required": ["title", "content"]
            }
        }
    })
    @xml_schema(
        tag_name="generate-pdf-report",
        mappings=[
            {"param_name": "title", "node_type": "element", "path": "title"},
            {"param_name": "content", "node_type": "element", "path": "content"}
        ],
        example="""
<generate-pdf-report>
    <title>Top Healthcare Companies in the UK</title>
    <content>
        <section title="AstraZeneca">
            <item key="Market Cap">$150B</item>
            <item key="Revenue">$26.7B</item>
            <item key="Employees">70,000</item>
        </section>
        <section title="GlaxoSmithKline (GSK)">
            <item key="Market Cap">$98B</item>
            <item key="Revenue">$34.6B</item>
            <item key="Employees">105,000</item>
        </section>
    </content>
</generate-pdf-report>
"""
    )
    async def generate_pdf_report(self, title: str, content: str) -> ToolResult:
        """Generate a PDF report from structured data."""
        try:
            # Ensure sandbox is ready
            await self._ensure_sandbox()
            logger.info(f"Generating PDF report: {title}")
            
            # Build PDF in memory
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, 
                                  rightMargin=72, leftMargin=72,
                                  topMargin=72, bottomMargin=72)
            
            # Create styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'Title',
                parent=styles['Heading1'],
                fontSize=16,
                alignment=TA_CENTER,
                spaceAfter=20
            )
            heading_style = ParagraphStyle(
                'Heading',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=10,
                spaceBefore=15
            )
            normal_style = ParagraphStyle(
                'BodyText',
                parent=styles['Normal'],
                fontSize=10,
                spaceBefore=6
            )
            
            # Start with the title
            flowables = [
                Paragraph(title, title_style),
                Spacer(1, 20)
            ]
            
            # Process content - try to parse as XML or use as markdown
            try:
                # Check if content has XML-like structure
                if "<section" in content and "</section>" in content:
                    # Extract sections
                    import re
                    sections = re.findall(r'<section title="([^"]+)">(.*?)</section>', content, re.DOTALL)
                    
                    for section_title, section_content in sections:
                        # Add section title
                        flowables.append(Paragraph(section_title, heading_style))
                        flowables.append(Spacer(1, 10))
                        
                        # Extract items
                        items = re.findall(r'<item key="([^"]+)">(.*?)</item>', section_content, re.DOTALL)
                        
                        # Create table data
                        table_data = []
                        for key, value in items:
                            table_data.append([key, value.strip()])
                        
                        if table_data:
                            # Create table
                            table = Table(table_data, colWidths=[1.5*inch, 3*inch])
                            table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                                ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
                                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                                ('GRID', (0, 0), (-1, -1), 1, colors.black)
                            ]))
                            
                            flowables.append(table)
                            flowables.append(Spacer(1, 15))
                else:
                    # Handle as markdown/plain text
                    lines = content.split('\n')
                    for line in lines:
                        line = line.strip()
                        if not line:
                            flowables.append(Spacer(1, 10))
                            continue
                            
                        if line.startswith('# '):
                            # Title
                            flowables.append(Paragraph(line[2:], title_style))
                        elif line.startswith('## '):
                            # Heading
                            flowables.append(Paragraph(line[3:], heading_style))
                        elif line.startswith('### '):
                            # Subheading
                            flowables.append(Paragraph(line[4:], styles['Heading3']))
                        elif line.startswith('- '):
                            # Bullet point
                            flowables.append(Paragraph(f"• {line[2:]}", normal_style))
                        else:
                            # Normal text
                            flowables.append(Paragraph(line, normal_style))
            except Exception as e:
                logger.warning(f"Error parsing content structure: {str(e)}, treating as plain text")
                # Fallback to plain text
                flowables.append(Paragraph(content, normal_style))
            
            # Build the PDF
            doc.build(flowables)
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            # Save PDF in sandbox under /workspace/reports
            reports_dir = f"{self.workspace_path}/reports"
            try:
                self.sandbox.fs.create_folder(reports_dir, "755")
            except Exception:
                pass
            
            # Generate filename if not provided
            filename = f"{title.replace(' ', '_')}.pdf"
            path = f"{reports_dir}/{filename}"
            self.sandbox.fs.upload_file(path, pdf_bytes)
            logger.info(f"PDF report generated successfully at: {path}")
            
            return self.success_response(f"PDF report generated successfully. File name: \"{filename}\"")
        except Exception as e:
            logger.error(f"Error generating PDF report: {str(e)}")
            return self.fail_response(f"Error generating PDF report: {str(e)}")
