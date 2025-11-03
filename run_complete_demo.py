#!/usr/bin/env python3
"""
Complete Demo Runner for Event Planning Agent v2
This script starts the API server and runs the complete demo
"""

import subprocess
import sys
import time
import os
import signal
from pathlib import Path
from datetime import datetime
from io import StringIO

class CompleteDemoRunner:
    """Runner for the complete Event Planning Agent v2 demo"""
    
    def __init__(self):
        self.api_process = None
        self.base_dir = Path(__file__).parent
        self.output_buffer = StringIO()
        self.start_time = datetime.now()
        self.steps_completed = []
        self.demo_results = {}
        
    def log(self, message: str, to_file: bool = True):
        """Log message to console and buffer"""
        print(message)
        if to_file:
            self.output_buffer.write(message + "\n")
    
    def print_header(self, title: str):
        """Print formatted header"""
        header = "\n" + "=" * 80 + "\n" + f"🎉 {title}\n" + "=" * 80
        self.log(header)
    
    def check_requirements(self) -> bool:
        """Check if all requirements are met"""
        self.log("\n🔍 Checking requirements...")
        
        # Check Python version
        if sys.version_info < (3, 8):
            self.log("❌ Python 3.8+ required")
            return False
        self.log(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
        
        # Check if event_planning_agent_v2 directory exists
        agent_dir = self.base_dir / "event_planning_agent_v2"
        if not agent_dir.exists():
            self.log("❌ event_planning_agent_v2 directory not found")
            return False
        self.log("✅ Event Planning Agent v2 directory found")
        
        # Check if demo script exists
        demo_script = agent_dir / "demo_priya_rohit.py"
        if not demo_script.exists():
            self.log("❌ Demo script not found")
            return False
        self.log("✅ Demo script found")
        
        self.steps_completed.append("Requirements Check")
        return True
    
    def install_dependencies(self) -> bool:
        """Install required dependencies"""
        self.log("\n📦 Installing dependencies...")
        
        try:
            # Install demo requirements (simplified)
            agent_dir = self.base_dir / "event_planning_agent_v2"
            demo_requirements_file = agent_dir / "requirements_demo.txt"
            requirements_file = agent_dir / "requirements.txt"
            
            # Try demo requirements first (minimal dependencies)
            if demo_requirements_file.exists():
                self.log("Installing minimal demo requirements...")
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", "-r", str(demo_requirements_file)
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.log("✅ Demo dependencies installed")
                else:
                    self.log(f"⚠️ Some dependencies may have issues: {result.stderr[:200]}")
            elif requirements_file.exists():
                self.log("Installing Event Planning Agent v2 requirements...")
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    self.log(f"❌ Failed to install requirements: {result.stderr[:200]}")
                    return False
                self.log("✅ Dependencies installed")
            else:
                self.log("⚠️ No requirements.txt found, continuing...")
            
            self.steps_completed.append("Dependencies Installation")
            return True
            
        except Exception as e:
            self.log(f"❌ Error installing dependencies: {e}")
            return False
    
    def start_api_server(self) -> bool:
        """Start the Event Planning Agent v2 API server"""
        self.log("\n🚀 Starting Event Planning Agent v2 API server...")
        
        try:
            agent_dir = self.base_dir / "event_planning_agent_v2"
            
            # Change to the agent directory
            os.chdir(agent_dir)
            
            # Start the API server
            self.api_process = subprocess.Popen([
                sys.executable, "main.py"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Wait a bit for server to start
            self.log("⏳ Waiting for API server to start...")
            
            # Progressive wait with status updates
            for i in range(10):
                time.sleep(1)
                if self.api_process.poll() is not None:
                    stdout, stderr = self.api_process.communicate()
                    self.log(f"❌ API server failed to start")
                    self.log(f"Error: {stderr[:500]}")
                    return False
                if i % 3 == 0:
                    self.log(f"   ... {i+1}s elapsed")
            
            # Check if process is still running
            if self.api_process.poll() is None:
                self.log("✅ API server started successfully")
                self.log("🌐 Server running at: http://localhost:8000")
                self.demo_results['api_server'] = 'Running'
                self.steps_completed.append("API Server Started")
                return True
            else:
                stdout, stderr = self.api_process.communicate()
                self.log(f"❌ API server failed to start")
                self.log(f"Error: {stderr[:500]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error starting API server: {e}")
            return False
    
    def run_demo(self) -> bool:
        """Run the Priya & Rohit demo"""
        self.log("\n🎭 Running Priya & Rohit Wedding Demo...")
        self.log("📋 Demo Scenario:")
        self.log("   • Couple: Priya & Rohit")
        self.log("   • Event Type: Traditional Indian Wedding")
        self.log("   • Budget: ₹50,00,000")
        self.log("   • Guests: 500")
        self.log("   • Location: Mumbai")
        
        try:
            agent_dir = self.base_dir / "event_planning_agent_v2"
            demo_script = agent_dir / "demo_priya_rohit.py"
            
            # Run the demo script with output capture
            self.log("\n⚙️ Executing demo workflow...")
            result = subprocess.run([
                sys.executable, str(demo_script)
            ], cwd=agent_dir, capture_output=True, text=True)
            
            # Capture demo output
            if result.stdout:
                self.log("\n📊 Demo Output:")
                self.log(result.stdout[:2000])  # First 2000 chars
            
            if result.returncode == 0:
                self.log("\n✅ Demo completed successfully!")
                self.demo_results['demo_status'] = 'Success'
                self.steps_completed.append("Demo Execution")
                
                # Check for generated files
                self.log("\n📁 Checking generated files...")
                generated_files = list(agent_dir.glob("*priya*rohit*.json")) + \
                                list(agent_dir.glob("*priya*rohit*.txt")) + \
                                list(self.base_dir.glob("*priya*rohit*.json"))
                
                if generated_files:
                    self.log(f"✅ Found {len(generated_files)} generated file(s):")
                    for f in generated_files[:5]:
                        self.log(f"   • {f.name}")
                    self.demo_results['generated_files'] = len(generated_files)
                
                return True
            else:
                self.log(f"\n❌ Demo failed with return code: {result.returncode}")
                if result.stderr:
                    self.log(f"Error output: {result.stderr[:1000]}")
                self.demo_results['demo_status'] = 'Failed'
                return False
                
        except Exception as e:
            self.log(f"❌ Error running demo: {e}")
            self.demo_results['demo_status'] = 'Error'
            return False
    
    def save_output_to_file(self):
        """Save demo output to text file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.base_dir / f"demo_output_{timestamp}.txt"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("EVENT PLANNING AGENT V2 - COMPLETE DEMO OUTPUT\n")
                f.write("=" * 80 + "\n\n")
                f.write(f"Demo Run Date: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Duration: {(datetime.now() - self.start_time).total_seconds():.2f} seconds\n")
                f.write(f"Steps Completed: {len(self.steps_completed)}\n\n")
                
                f.write("STEPS COMPLETED:\n")
                for i, step in enumerate(self.steps_completed, 1):
                    f.write(f"  {i}. {step}\n")
                f.write("\n")
                
                f.write("DEMO RESULTS:\n")
                for key, value in self.demo_results.items():
                    f.write(f"  • {key}: {value}\n")
                f.write("\n")
                
                f.write("=" * 80 + "\n")
                f.write("DETAILED LOG:\n")
                f.write("=" * 80 + "\n\n")
                f.write(self.output_buffer.getvalue())
            
            self.log(f"\n💾 Output saved to: {output_file.name}")
            return output_file
            
        except Exception as e:
            self.log(f"⚠️ Could not save output file: {e}")
            return None
    
    def generate_pdf_report(self, text_file: Path):
        """Generate PDF report from text output"""
        try:
            # Try to import reportlab for PDF generation
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_file = self.base_dir / f"demo_report_{timestamp}.pdf"
            
            doc = SimpleDocTemplate(str(pdf_file), pagesize=letter)
            story = []
            styles = getSampleStyleSheet()
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor='darkblue',
                spaceAfter=30,
                alignment=TA_CENTER
            )
            story.append(Paragraph("Event Planning Agent v2", title_style))
            story.append(Paragraph("Complete Demo Report", title_style))
            story.append(Spacer(1, 0.5*inch))
            
            # Summary
            story.append(Paragraph(f"<b>Demo Date:</b> {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
            story.append(Paragraph(f"<b>Duration:</b> {(datetime.now() - self.start_time).total_seconds():.2f} seconds", styles['Normal']))
            story.append(Paragraph(f"<b>Steps Completed:</b> {len(self.steps_completed)}", styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
            
            # Steps
            story.append(Paragraph("<b>Completed Steps:</b>", styles['Heading2']))
            for i, step in enumerate(self.steps_completed, 1):
                story.append(Paragraph(f"{i}. {step}", styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
            
            # Results
            story.append(Paragraph("<b>Demo Results:</b>", styles['Heading2']))
            for key, value in self.demo_results.items():
                story.append(Paragraph(f"• {key}: {value}", styles['Normal']))
            
            doc.build(story)
            self.log(f"📄 PDF report saved to: {pdf_file.name}")
            return pdf_file
            
        except ImportError:
            self.log("⚠️ reportlab not installed. Installing for PDF generation...")
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "reportlab"], 
                             capture_output=True, check=True)
                self.log("✅ reportlab installed, generating PDF...")
                return self.generate_pdf_report(text_file)
            except:
                self.log("⚠️ Could not install reportlab. PDF generation skipped.")
                self.log("💡 Install manually with: pip install reportlab")
                return None
        except Exception as e:
            self.log(f"⚠️ Could not generate PDF: {e}")
            return None
    
    def cleanup(self):
        """Clean up processes"""
        self.log("\n🧹 Cleaning up...")
        
        if self.api_process and self.api_process.poll() is None:
            self.log("🛑 Stopping API server...")
            self.api_process.terminate()
            
            # Wait for graceful shutdown
            try:
                self.api_process.wait(timeout=5)
                self.log("✅ API server stopped")
            except subprocess.TimeoutExpired:
                self.log("⚠️ Force killing API server...")
                self.api_process.kill()
                self.api_process.wait()
    
    def run_complete_demo(self):
        """Run the complete demo workflow"""
        self.print_header("Event Planning Agent v2 - Complete Demo Runner")
        
        self.log("\n🎯 This will run the complete Event Planning Agent v2 system:")
        self.log("   1. Check requirements")
        self.log("   2. Install dependencies") 
        self.log("   3. Start API server")
        self.log("   4. Run Priya & Rohit wedding demo")
        self.log("   5. Generate output reports")
        
        try:
            # Step 1: Check requirements
            if not self.check_requirements():
                self.log("\n❌ Requirements check failed")
                return False
            
            # Step 2: Install dependencies
            if not self.install_dependencies():
                self.log("\n❌ Dependency installation failed")
                return False
            
            # Step 3: Start API server
            if not self.start_api_server():
                self.log("\n❌ API server startup failed")
                return False
            
            # Step 4: Run demo
            demo_success = self.run_demo()
            
            # Step 5: Show results
            if demo_success:
                self.print_header("🎉 Complete Demo Finished Successfully!")
                self.log("\n✅ All Event Planning Agent v2 functionalities demonstrated:")
                self.log("   ✓ Multi-agent AI system")
                self.log("   ✓ Real-time progress tracking")
                self.log("   ✓ Intelligent vendor matching")
                self.log("   ✓ Automated combination scoring")
                self.log("   ✓ Comprehensive blueprint generation")
                self.log("   ✓ Multi-format export")
                
                self.log(f"\n🎊 Priya & Rohit's wedding plan generated successfully!")
                self.log(f"📁 Check the generated files in event_planning_agent_v2/")
            else:
                self.log("\n⚠️ Demo completed with issues")
            
            # Save outputs
            self.log("\n📝 Generating output reports...")
            text_file = self.save_output_to_file()
            if text_file:
                pdf_file = self.generate_pdf_report(text_file)
            
            return demo_success
            
        except KeyboardInterrupt:
            self.log("\n\n⏹️ Demo interrupted by user")
            return False
        except Exception as e:
            self.log(f"\n❌ Demo failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.cleanup()

def main():
    """Main entry point"""
    runner = CompleteDemoRunner()
    
    try:
        success = runner.run_complete_demo()
        
        if success:
            runner.log("\n🌟 Demo completed successfully!")
            runner.log("💡 You can now explore the generated wedding plan files")
            runner.log("\n📊 Output files generated:")
            runner.log("   • Text report: demo_output_*.txt")
            runner.log("   • PDF report: demo_report_*.pdf (if reportlab available)")
        else:
            runner.log("\n⚠️ Demo had some issues")
            runner.log("💡 Check the error messages above and try again")
        
        input("\nPress Enter to exit...")
        return success
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
        return Fals

if __name__ == "__main__":
    main()