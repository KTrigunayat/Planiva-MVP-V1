#!/usr/bin/env python3
"""
Complete Event Management Platform Demo
Demonstrates Event Planning, CRM, and Task Management using Priya & Rohit's wedding data

This demo showcases:
1. Event Planning - AI-powered vendor sourcing and optimization
2. CRM - Client communication preferences and history
3. Task Management - Task tracking, timeline, conflicts, and vendor coordination
"""

import json
import sys
import time
import requests
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

class CompleteEventManagementDemo:
    """Complete demo for Event Planning Agent v2 with CRM and Task Management"""
    
    def __init__(self, client_data_path: str = "streamlit_gui/client_data.json"):
        self.api_base_url = "http://localhost:8000"
        self.client_data_path = client_data_path
        self.client_data = None
        self.plan_id = None
        self.client_id = None
        self.output_lines = []  # Store output for file generation
        self.demo_mode = True  # Always run in demo mode for better simulation
        
    def print_header(self, title: str, char: str = "="):
        """Print a formatted header"""
        line1 = "\n" + char * 80
        line2 = f"🎉 {title}"
        line3 = char * 80
        print(line1)
        print(line2)
        print(line3)
        self.output_lines.extend([line1, line2, line3])
    
    def print_section(self, title: str):
        """Print a formatted section header"""
        line1 = f"\n{'─' * 80}"
        line2 = f"📋 {title}"
        line3 = f"{'─' * 80}"
        print(line1)
        print(line2)
        print(line3)
        self.output_lines.extend([line1, line2, line3])
    
    def load_client_data(self) -> bool:
        """Load client data from JSON file"""
        self.print_section("Loading Client Data")
        
        try:
            with open(self.client_data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.client_data = data.get('form_data', data)
            
            msg1 = f"✅ Client data loaded successfully"
            msg2 = f"   👰 Client: {self.client_data.get('client_name', 'N/A')}"
            msg3 = f"   📧 Email: {self.client_data.get('client_email', 'N/A')}"
            msg4 = f"   📅 Event Date: {self.client_data.get('event_date', 'N/A')}"
            msg5 = f"   📍 Location: {self.client_data.get('location', 'N/A')}"
            msg6 = f"   👥 Guests: {self.client_data.get('total_guests', 'N/A')}"
            msg7 = f"   💰 Budget: ₹{self.client_data.get('total_budget', 0):,.0f}"
            print(msg1)
            print(msg2)
            print(msg3)
            print(msg4)
            print(msg5)
            print(msg6)
            print(msg7)
            self.output_lines.extend([msg1, msg2, msg3, msg4, msg5, msg6, msg7])
            
            self.client_id = self.client_data.get('client_email', 'priya.rohit@email.com')
            return True
            
        except FileNotFoundError:
            print(f"❌ Client data file not found: {self.client_data_path}")
            return False
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in client data file: {e}")
            return False
        except Exception as e:
            print(f"❌ Error loading client data: {e}")
            return False
    
    def check_api_health(self) -> bool:
        """Check if the API is running"""
        self.print_section("API Health Check")
        
        if self.demo_mode:
            msg1 = "🎭 Running in DEMO MODE with simulated responses"
            msg2 = "✅ Demo API Status: Active"
            msg3 = "📊 Demo Version: v2.0.0"
            msg4 = f"🕐 Timestamp: {datetime.now().isoformat()}"
            print(msg1)
            print(msg2)
            print(msg3)
            print(msg4)
            self.output_lines.extend([msg1, msg2, msg3, msg4])
            time.sleep(0.5)
            return True
        
        try:
            response = requests.get(f"{self.api_base_url}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                msg1 = f"✅ API Status: {health_data.get('status', 'unknown')}"
                msg2 = f"📊 Version: {health_data.get('version', 'unknown')}"
                msg3 = f"🕐 Timestamp: {health_data.get('timestamp', 'unknown')}"
                print(msg1)
                print(msg2)
                print(msg3)
                self.output_lines.extend([msg1, msg2, msg3])
                return True
            else:
                msg = f"❌ API Health Check Failed: Status {response.status_code}"
                print(msg)
                self.output_lines.append(msg)
                return False
        except requests.exceptions.RequestException as e:
            msg1 = f"⚠️ API Connection Failed: {e}"
            msg2 = "🔄 Running in demo mode with simulated responses..."
            print(msg1)
            print(msg2)
            self.output_lines.extend([msg1, msg2])
            self.demo_mode = True
            return False
    
    # ==================== EVENT PLANNING ====================
    
    def demo_event_planning(self) -> bool:
        """Demonstrate event planning functionality"""
        self.print_header("PART 1: EVENT PLANNING", "=")
        
        # Step 1: Create Event Plan
        if not self.create_event_plan():
            return False
        
        # Step 2: Monitor Progress
        if not self.monitor_planning_progress():
            return False
        
        # Step 3: Get Vendor Combinations
        combinations = self.get_vendor_combinations()
        if not combinations:
            return False
        
        # Step 4: Select Best Combination
        if not self.select_best_combination(combinations):
            return False
        
        # Step 5: Generate Blueprint
        blueprint = self.generate_final_blueprint()
        if not blueprint:
            return False
        
        # Step 6: Export Blueprint
        self.export_blueprint(blueprint)
        
        msg = "\n✅ Event Planning Phase Complete!"
        print(msg)
        self.output_lines.append(msg)
        return True
    
    def create_event_plan(self) -> bool:
        """Create a new event plan"""
        self.print_section("Creating Event Plan")
        
        # Transform client data to API format
        api_data = self.transform_to_api_format(self.client_data)
        
        try:
            request_lines = [
                "📤 Sending event planning request...",
                f"   Event Type: {api_data.get('eventType')}",
                f"   Guest Count: {api_data.get('guestCount', {}).get('total', 0)}",
                f"   Budget: ₹{api_data.get('budget', 0):,.0f}"
            ]
            for line in request_lines:
                print(line)
            self.output_lines.extend(request_lines)
            
            response = requests.post(
                f"{self.api_base_url}/v1/plans",
                json=api_data,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                plan_response = response.json()
                self.plan_id = plan_response.get('plan_id')
                success_lines = [
                    f"✅ Event plan created successfully!",
                    f"🆔 Plan ID: {self.plan_id}"
                ]
                for line in success_lines:
                    print(line)
                self.output_lines.extend(success_lines)
                return True
            else:
                msg = f"❌ Failed to create plan: Status {response.status_code}"
                print(msg)
                self.output_lines.append(msg)
                return False
                
        except requests.exceptions.RequestException as e:
            # Generate demo plan ID for offline mode
            self.plan_id = f"demo_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            demo_lines = [
                f"🎭 Demo Mode: Using plan ID {self.plan_id}",
                f"✅ Event plan created successfully in demo mode!"
            ]
            for line in demo_lines:
                print(line)
            self.output_lines.extend(demo_lines)
            return True
    
    def transform_to_api_format(self, client_data: Dict) -> Dict:
        """Transform client data to API format"""
        return {
            "clientName": client_data.get('client_name'),
            "clientEmail": client_data.get('client_email'),
            "clientPhone": client_data.get('client_phone'),
            "eventType": client_data.get('event_type'),
            "eventDate": client_data.get('event_date'),
            "location": client_data.get('location'),
            "guestCount": {
                "total": client_data.get('total_guests'),
                "Reception": client_data.get('reception_guests', client_data.get('total_guests')),
                "Ceremony": client_data.get('ceremony_guests', client_data.get('total_guests'))
            },
            "budget": client_data.get('total_budget'),
            "budgetFlexibility": client_data.get('budget_flexibility', 'moderate'),
            "clientVision": client_data.get('client_vision'),
            "venuePreferences": client_data.get('venue_types', []),
            "essentialVenueAmenities": client_data.get('essential_amenities', []),
            "decorationAndAmbiance": {
                "desiredTheme": client_data.get('event_theme'),
                "colorScheme": client_data.get('color_scheme', '').split(', ') if isinstance(client_data.get('color_scheme'), str) else client_data.get('color_scheme', []),
                "stylePreferences": client_data.get('style_preferences', [])
            },
            "foodAndCatering": {
                "cuisinePreferences": client_data.get('cuisine_preferences', []),
                "dietaryOptions": client_data.get('dietary_restrictions', []),
                "serviceStyle": client_data.get('service_style', 'buffet'),
                "beverages": {"allowed": client_data.get('beverages_allowed', False)}
            },
            "additionalRequirements": {
                "photography": f"{', '.join(client_data.get('photography_style', []))} photography" if client_data.get('photography_needed') else None,
                "makeup": f"{', '.join(client_data.get('makeup_style', []))} makeup" if client_data.get('makeup_needed') else None,
                "videography": "Professional videography" if client_data.get('videography_needed') else None
            },
            "priorities": client_data.get('priorities', {})
        }
    
    def monitor_planning_progress(self) -> bool:
        """Monitor the planning progress"""
        self.print_section("Monitoring Planning Progress")
        
        workflow_lines = [
            "🔄 AI Agents working on your event plan...",
            "💡 This demonstrates the multi-agent workflow:",
            "   🤖 Orchestrator Agent - Coordinating the workflow",
            "   🤖 Budgeting Agent - Analyzing budget allocation",
            "   🤖 Sourcing Agent - Finding matching vendors",
            "   🤖 Optimization Agent - Creating combinations",
            "   🤖 Scoring Agent - Ranking options"
        ]
        for line in workflow_lines:
            print(line)
        self.output_lines.extend(workflow_lines)
        
        # Simulate progress for demo
        steps = [
            ("initializing", "Starting workflow", 10),
            ("budget_analysis", "Analyzing budget", 25),
            ("vendor_sourcing", "Finding vendors", 50),
            ("combination_generation", "Creating combinations", 75),
            ("scoring", "Ranking options", 90),
            ("completed", "Plan complete", 100)
        ]
        
        for status, desc, progress in steps:
            msg = f"   Progress: {progress}% - {desc}..."
            print(f"\r{msg}", end="", flush=True)
            time.sleep(0.8)
        
        msg = f"\n✅ Planning completed successfully!"
        print(msg)
        self.output_lines.append(msg)
        return True
    
    def get_vendor_combinations(self) -> List[Dict]:
        """Get vendor combinations"""
        self.print_section("Retrieving Vendor Combinations")
        
        # Demo combinations based on Priya & Rohit's requirements
        combinations = self.create_demo_combinations()
        
        msg = f"✅ Retrieved {len(combinations)} vendor combinations"
        print(msg)
        self.output_lines.append(msg)
        
        for i, combo in enumerate(combinations[:3], 1):
            lines = [
                f"\n� ComVbination {i}:",
                f"   💯 Fitness Score: {combo.get('fitness_score', 0):.1f}%",
                f"   � Totaol Cost: ₹{combo.get('total_cost', 0):,.0f}",
                f"   🏢 Venue: {combo.get('venue', {}).get('name', 'N/A')}",
                f"   🍽️ Caterer: {combo.get('caterer', {}).get('name', 'N/A')}",
                f"   📸 Photographer: {combo.get('photographer', {}).get('name', 'N/A')}",
                f"   💄 Makeup: {combo.get('makeup_artist', {}).get('name', 'N/A')}"
            ]
            for line in lines:
                print(line)
            self.output_lines.extend(lines)
        
        return combinations
    
    def select_best_combination(self, combinations: List[Dict]) -> bool:
        """Select the best vendor combination"""
        self.print_section("Selecting Best Combination")
        
        best_combo = max(combinations, key=lambda x: x.get('fitness_score', 0))
        
        lines = [
            f"✅ Selected combination with highest fitness score",
            f"   💯 Fitness Score: {best_combo.get('fitness_score', 0):.1f}%",
            f"   � T otal Cost: ₹{best_combo.get('total_cost', 0):,.0f}",
            f"   📊 Budget Utilization: {(best_combo.get('total_cost', 0) / self.client_data.get('total_budget', 1) * 100):.1f}%"
        ]
        for line in lines:
            print(line)
        self.output_lines.extend(lines)
        
        return True
    
    def generate_final_blueprint(self) -> Dict:
        """Generate the final event blueprint"""
        self.print_section("Generating Final Blueprint")
        
        blueprint = {
            'plan_id': self.plan_id,
            'client_info': {
                'name': self.client_data.get('client_name'),
                'email': self.client_data.get('client_email'),
                'phone': self.client_data.get('client_phone')
            },
            'event_details': {
                'type': self.client_data.get('event_type'),
                'date': self.client_data.get('event_date'),
                'location': self.client_data.get('location'),
                'guests': self.client_data.get('total_guests'),
                'theme': self.client_data.get('event_theme'),
                'color_scheme': self.client_data.get('color_scheme')
            },
            'budget': {
                'total': self.client_data.get('total_budget'),
                'allocated': self.client_data.get('budget_allocation', {})
            },
            'generated_at': datetime.now().isoformat()
        }
        
        lines = [
            "✅ Final blueprint generated successfully!",
            f"   📋 Plan ID: {blueprint['plan_id']}",
            f"   � Client:  {blueprint['client_info']['name']}",
            f"   📅 Event Date: {blueprint['event_details']['date']}",
            f"   💰 Budget: ₹{blueprint['budget']['total']:,.0f}"
        ]
        for line in lines:
            print(line)
        self.output_lines.extend(lines)
        
        return blueprint
    
    def export_blueprint(self, blueprint: Dict):
        """Export blueprint to file"""
        self.print_section("Exporting Blueprint")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"event_blueprint_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(blueprint, f, indent=2, ensure_ascii=False)
            
            msg = f"✅ Blueprint exported: {filename}"
            print(msg)
            self.output_lines.append(msg)
        except Exception as e:
            msg = f"⚠️ Export failed: {e}"
            print(msg)
            self.output_lines.append(msg)
    
    # ==================== CRM & COMMUNICATIONS ====================
    
    def demo_crm_communications(self) -> bool:
        """Demonstrate CRM and communication management"""
        self.print_header("PART 2: CRM & COMMUNICATION MANAGEMENT", "=")
        
        # Step 1: Set Communication Preferences
        if not self.set_communication_preferences():
            return False
        
        # Step 2: View Communication History
        if not self.view_communication_history():
            return False
        
        # Step 3: Analyze Communication Analytics
        if not self.analyze_communication_analytics():
            return False
        
        msg = "\n✅ CRM & Communication Phase Complete!"
        print(msg)
        self.output_lines.append(msg)
        return True
    
    def set_communication_preferences(self) -> bool:
        """Set client communication preferences"""
        self.print_section("Setting Communication Preferences")
        
        preferences = {
            'client_id': self.client_id,
            'preferred_channels': ['Email', 'SMS', 'WhatsApp'],
            'timezone': 'Asia/Kolkata',
            'quiet_hours': {
                'start': '22:00',
                'end': '08:00'
            },
            'opt_outs': {
                'email': False,
                'sms': False,
                'whatsapp': False
            },
            'language': 'en',
            'notification_preferences': {
                'budget_updates': True,
                'vendor_confirmations': True,
                'timeline_changes': True,
                'reminders': True
            }
        }
        
        try:
            response = requests.post(
                f"{self.api_base_url}/api/crm/preferences",
                json=preferences,
                timeout=10
            )
            
            if response.status_code == 200:
                msg = "✅ Communication preferences set successfully"
                print(msg)
                self.output_lines.append(msg)
            else:
                msg = f"⚠️ API call failed, using demo mode"
                print(msg)
                self.output_lines.append(msg)
        except:
            msg = "🎭 Demo Mode: Preferences configured"
            print(msg)
            self.output_lines.append(msg)
        
        lines = [
            f"   📧 Preferred Channels: {', '.join(preferences['preferred_channels'])}",
            f"   � Timezeone: {preferences['timezone']}",
            f"   🌙 Quiet Hours: {preferences['quiet_hours']['start']} - {preferences['quiet_hours']['end']}",
            f"   🔔 Notifications: Enabled for all event updates"
        ]
        for line in lines:
            print(line)
        self.output_lines.extend(lines)
        
        return True
    
    def view_communication_history(self) -> bool:
        """View communication history"""
        self.print_section("Communication History")
        
        # Demo communication history
        communications = [
            {
                'id': 'comm_001',
                'type': 'welcome',
                'channel': 'Email',
                'status': 'delivered',
                'subject': 'Welcome to Event Planning Agent!',
                'sent_at': (datetime.now() - timedelta(hours=2)).isoformat(),
                'delivered_at': (datetime.now() - timedelta(hours=2, minutes=-5)).isoformat(),
                'opened': True,
                'opened_at': (datetime.now() - timedelta(hours=1, minutes=45)).isoformat()
            },
            {
                'id': 'comm_002',
                'type': 'budget_summary',
                'channel': 'Email',
                'status': 'delivered',
                'subject': 'Your Event Budget Summary',
                'sent_at': (datetime.now() - timedelta(hours=1)).isoformat(),
                'delivered_at': (datetime.now() - timedelta(hours=1, minutes=-3)).isoformat(),
                'opened': True,
                'opened_at': (datetime.now() - timedelta(minutes=45)).isoformat()
            },
            {
                'id': 'comm_003',
                'type': 'vendor_options',
                'channel': 'SMS',
                'status': 'delivered',
                'subject': 'Vendor combinations ready!',
                'sent_at': (datetime.now() - timedelta(minutes=30)).isoformat(),
                'delivered_at': (datetime.now() - timedelta(minutes=30, seconds=-10)).isoformat()
            },
            {
                'id': 'comm_004',
                'type': 'confirmation',
                'channel': 'WhatsApp',
                'status': 'delivered',
                'subject': 'Event plan confirmed',
                'sent_at': (datetime.now() - timedelta(minutes=10)).isoformat(),
                'delivered_at': (datetime.now() - timedelta(minutes=10, seconds=-5)).isoformat()
            }
        ]
        
        lines = [
            f"✅ Retrieved {len(communications)} communications",
            f"\n📨 Recent Communications:"
        ]
        for line in lines:
            print(line)
        self.output_lines.extend(lines)
        
        for comm in communications:
            status_icon = "✅" if comm['status'] == 'delivered' else "📤"
            channel_icon = {"Email": "📧", "SMS": "📱", "WhatsApp": "💬"}.get(comm['channel'], "📨")
            
            comm_lines = [
                f"\n   {status_icon} {channel_icon} {comm['type'].replace('_', ' ').title()}",
                f"      Channel: {comm['channel']}",
                f"      Status: {comm['status'].title()}",
                f"      Sent: {comm['sent_at'][:19]}"
            ]
            if comm.get('opened'):
                comm_lines.append(f"      ✓ Opened: {comm['opened_at'][:19]}")
            
            for line in comm_lines:
                print(line)
            self.output_lines.extend(comm_lines)
        
        return True
    
    def analyze_communication_analytics(self) -> bool:
        """Analyze communication analytics"""
        self.print_section("Communication Analytics")
        
        analytics = {
            'total_sent': 4,
            'total_delivered': 4,
            'total_opened': 2,
            'total_clicked': 1,
            'total_failed': 0,
            'delivery_rate': 100.0,
            'open_rate': 50.0,
            'click_rate': 25.0,
            'by_channel': {
                'Email': {'sent': 2, 'delivered': 2, 'opened': 2, 'clicked': 1},
                'SMS': {'sent': 1, 'delivered': 1, 'opened': 0, 'clicked': 0},
                'WhatsApp': {'sent': 1, 'delivered': 1, 'opened': 0, 'clicked': 0}
            },
            'by_type': {
                'welcome': {'sent': 1, 'delivered': 1, 'opened': 1},
                'budget_summary': {'sent': 1, 'delivered': 1, 'opened': 1},
                'vendor_options': {'sent': 1, 'delivered': 1, 'opened': 0},
                'confirmation': {'sent': 1, 'delivered': 1, 'opened': 0}
            }
        }
        
        lines = [
            "✅ Communication Analytics Summary",
            f"\n📊 Overall Metrics:",
            f"   Total Sent: {analytics['total_sent']}",
            f"   Total Delivered: {analytics['total_delivered']} ({analytics['delivery_rate']:.1f}%)",
            f"   Total Opened: {analytics['total_opened']} ({analytics['open_rate']:.1f}%)",
            f"   Total Clicked: {analytics['total_clicked']} ({analytics['click_rate']:.1f}%)",
            f"   Failed: {analytics['total_failed']}",
            f"\n� Perfofrmance by Channel:"
        ]
        for line in lines:
            print(line)
        self.output_lines.extend(lines)
        
        for channel, stats in analytics['by_channel'].items():
            channel_lines = [
                f"   {channel}:",
                f"      Sent: {stats['sent']}, Delivered: {stats['delivered']}"
            ]
            if channel == 'Email':
                channel_lines.append(f"      Opened: {stats['opened']}, Clicked: {stats['clicked']}")
            for line in channel_lines:
                print(line)
            self.output_lines.extend(channel_lines)
        
        insight_lines = [
            f"\n💡 Insights:",
            f"   ✓ 100% delivery rate - excellent!",
            f"   ✓ Email engagement is strong (50% open rate)",
            f"   ✓ All channels working effectively",
            f"   ✓ Client is actively engaged with communications"
        ]
        for line in insight_lines:
            print(line)
        self.output_lines.extend(insight_lines)
        
        return True
    
    # ==================== TASK MANAGEMENT ====================
    
    def demo_task_management(self) -> bool:
        """Demonstrate task management functionality"""
        self.print_header("PART 3: TASK MANAGEMENT", "=")
        
        # Step 1: View Extended Task List
        if not self.view_extended_task_list():
            return False
        
        # Step 2: View Timeline
        if not self.view_timeline():
            return False
        
        # Step 3: Check for Conflicts
        if not self.check_conflicts():
            return False
        
        # Step 4: View Vendor Assignments
        if not self.view_vendor_assignments():
            return False
        
        msg = "\n✅ Task Management Phase Complete!"
        print(msg)
        self.output_lines.append(msg)
        return True
    
    def view_extended_task_list(self) -> bool:
        """View extended task list with dependencies"""
        self.print_section("Extended Task List")
        
        tasks = self.create_demo_tasks()
        
        lines = [
            f"✅ Retrieved {len(tasks)} tasks",
            f"\n📋 Task Overview:"
        ]
        for line in lines:
            print(line)
        self.output_lines.extend(lines)
        
        # Group by priority
        by_priority = {'Critical': [], 'High': [], 'Medium': [], 'Low': []}
        for task in tasks:
            by_priority[task['priority']].append(task)
        
        for priority, task_list in by_priority.items():
            if task_list:
                priority_icon = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}[priority]
                priority_line = f"\n   {priority_icon} {priority} Priority ({len(task_list)} tasks):"
                print(priority_line)
                self.output_lines.append(priority_line)
                
                for task in task_list[:3]:  # Show first 3
                    status_icon = {"Pending": "⏳", "In Progress": "🔄", "Completed": "✅"}[task['status']]
                    task_lines = [
                        f"      {status_icon} {task['name']}",
                        f"         Duration: {task['duration']} min | Vendor: {task['vendor']}"
                    ]
                    for line in task_lines:
                        print(line)
                    self.output_lines.extend(task_lines)
        
        # Show statistics
        total = len(tasks)
        completed = len([t for t in tasks if t['status'] == 'Completed'])
        in_progress = len([t for t in tasks if t['status'] == 'In Progress'])
        pending = len([t for t in tasks if t['status'] == 'Pending'])
        
        stat_lines = [
            f"\n📊 Task Statistics:",
            f"   Total Tasks: {total}",
            f"   ✅ Completed: {completed} ({completed/total*100:.1f}%)",
            f"   🔄 In Progress: {in_progress} ({in_progress/total*100:.1f}%)",
            f"   ⏳ Pending: {pending} ({pending/total*100:.1f}%)"
        ]
        for line in stat_lines:
            print(line)
        self.output_lines.extend(stat_lines)
        
        return True
    
    def view_timeline(self) -> bool:
        """View timeline visualization"""
        self.print_section("Timeline Visualization")
        
        lines = [
            "✅ Timeline Gantt Chart Generated",
            f"\n📅 Event Timeline Overview:"
        ]
        for line in lines:
            print(line)
        self.output_lines.extend(lines)
        
        # Show key milestones
        event_date = datetime.fromisoformat(self.client_data.get('event_date'))
        milestones = [
            (event_date - timedelta(days=60), "Venue booking deadline"),
            (event_date - timedelta(days=45), "Catering menu finalization"),
            (event_date - timedelta(days=30), "Photography session booking"),
            (event_date - timedelta(days=14), "Final guest count confirmation"),
            (event_date - timedelta(days=7), "Final vendor confirmations"),
            (event_date - timedelta(days=1), "Final setup and preparation"),
            (event_date, "🎉 WEDDING DAY 🎉")
        ]
        
        for date, milestone in milestones:
            days_until = (date - datetime.now()).days
            if days_until > 0:
                line = f"   📍 {date.strftime('%Y-%m-%d')} ({days_until} days): {milestone}"
            elif days_until == 0:
                line = f"   🎊 {date.strftime('%Y-%m-%d')} (TODAY): {milestone}"
            else:
                line = f"   ✓ {date.strftime('%Y-%m-%d')} (completed): {milestone}"
            print(line)
            self.output_lines.append(line)
        
        feature_lines = [
            f"\n💡 Timeline Features:",
            f"   ✓ Color-coded by priority (Critical=Red, High=Orange, Medium=Yellow, Low=Green)",
            f"   ✓ Shows task dependencies and relationships",
            f"   ✓ Identifies overlapping tasks and conflicts",
            f"   ✓ Interactive zoom controls (Day/Week/Month view)"
        ]
        for line in feature_lines:
            print(line)
        self.output_lines.extend(feature_lines)
        
        return True
    
    def check_conflicts(self) -> bool:
        """Check for task conflicts"""
        self.print_section("Conflict Detection & Resolution")
        
        conflicts = [
            {
                'id': 'conflict_001',
                'type': 'Timeline Overlap',
                'severity': 'Medium',
                'description': 'Photographer and makeup artist both scheduled at 10:00 AM',
                'affected_tasks': ['Bridal makeup', 'Getting ready photos'],
                'suggested_resolution': 'Start makeup at 8:00 AM, photography at 10:00 AM'
            },
            {
                'id': 'conflict_002',
                'type': 'Venue Conflict',
                'severity': 'Low',
                'description': 'Ceremony setup overlaps with venue decoration',
                'affected_tasks': ['Venue decoration', 'Ceremony setup'],
                'suggested_resolution': 'Complete decoration by 2:00 PM, start ceremony setup at 2:30 PM'
            }
        ]
        
        if conflicts:
            msg = f"⚠️ Found {len(conflicts)} potential conflicts"
            print(msg)
            self.output_lines.append(msg)
            
            for i, conflict in enumerate(conflicts, 1):
                severity_icon = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}[conflict['severity']]
                conflict_lines = [
                    f"\n   {severity_icon} Conflict {i}: {conflict['type']}",
                    f"      Severity: {conflict['severity']}",
                    f"      Issue: {conflict['description']}",
                    f"      Affected: {', '.join(conflict['affected_tasks'])}",
                    f"      💡 Suggested Fix: {conflict['suggested_resolution']}"
                ]
                for line in conflict_lines:
                    print(line)
                self.output_lines.extend(conflict_lines)
            
            resolution_lines = [
                f"\n✅ Conflict Resolution Options:",
                f"   1. Apply suggested resolutions automatically",
                f"   2. Manually adjust task schedules",
                f"   3. Contact vendors to negotiate timing",
                f"   4. Review and resolve in Timeline view"
            ]
            for line in resolution_lines:
                print(line)
            self.output_lines.extend(resolution_lines)
        else:
            no_conflict_lines = [
                "✅ No conflicts detected!",
                "   All tasks are properly scheduled",
                "   No resource conflicts",
                "   No timeline overlaps"
            ]
            for line in no_conflict_lines:
                print(line)
            self.output_lines.extend(no_conflict_lines)
        
        return True
    
    def view_vendor_assignments(self) -> bool:
        """View vendor assignments and workload"""
        self.print_section("Vendor Assignments & Workload")
        
        vendors = [
            {
                'name': 'Grand Banquet Hall Bangalore',
                'type': 'Venue',
                'contact': '+91-80-12345678',
                'email': 'events@grandbanquet.com',
                'fitness_score': 92.5,
                'workload': 'Medium',
                'assigned_tasks': 5,
                'tasks': ['Venue setup', 'Ceremony space preparation', 'Reception area setup', 'Cleanup', 'Coordination']
            },
            {
                'name': 'Royal South Indian Caterers',
                'type': 'Caterer',
                'contact': '+91-98765-43210',
                'email': 'bookings@royalcaterers.com',
                'fitness_score': 95.0,
                'workload': 'High',
                'assigned_tasks': 8,
                'tasks': ['Menu planning', 'Food preparation', 'Service setup', 'Buffet service', 'Cleanup', 'Staff coordination', 'Quality control', 'Guest service']
            },
            {
                'name': 'Traditional Moments Photography',
                'type': 'Photographer',
                'contact': '+91-99876-54321',
                'email': 'info@traditionalmoments.com',
                'fitness_score': 88.0,
                'workload': 'Medium',
                'assigned_tasks': 6,
                'tasks': ['Getting ready photos', 'Ceremony coverage', 'Family portraits', 'Reception photos', 'Candid shots', 'Photo editing']
            },
            {
                'name': 'Bridal Beauty Experts',
                'type': 'Makeup Artist',
                'contact': '+91-98765-12345',
                'email': 'bookings@bridalbeauty.com',
                'fitness_score': 90.0,
                'workload': 'Low',
                'assigned_tasks': 3,
                'tasks': ['Bridal makeup', 'Touch-ups', 'Bridal party makeup']
            }
        ]
        
        msg = f"✅ {len(vendors)} vendors assigned"
        print(msg)
        self.output_lines.append(msg)
        
        for vendor in vendors:
            workload_icon = {"Low": "🟢", "Medium": "🟡", "High": "🟠"}[vendor['workload']]
            vendor_lines = [
                f"\n   👥 {vendor['name']}",
                f"      Type: {vendor['type']}",
                f"      Contact: {vendor['contact']}",
                f"      Email: {vendor['email']}",
                f"      💯 Fitness Score: {vendor['fitness_score']:.1f}%",
                f"      {workload_icon} Workload: {vendor['workload']} ({vendor['assigned_tasks']} tasks)",
                f"      Tasks: {', '.join(vendor['tasks'][:3])}{'...' if len(vendor['tasks']) > 3 else ''}"
            ]
            for line in vendor_lines:
                print(line)
            self.output_lines.extend(vendor_lines)
        
        distribution_lines = [
            f"\n📊 Workload Distribution:",
            f"   High: 1 vendor (25%)",
            f"   Medium: 2 vendors (50%)",
            f"   Low: 1 vendor (25%)",
            f"\n💡 Workload is well-balanced across vendors"
        ]
        for line in distribution_lines:
            print(line)
        self.output_lines.extend(distribution_lines)
        
        return True
    
    # ==================== HELPER METHODS ====================
    
    def create_demo_combinations(self) -> List[Dict]:
        """Create demo vendor combinations"""
        return [
            {
                'combination_id': 'combo_001',
                'fitness_score': 92.5,
                'total_cost': 745000,
                'venue': {
                    'name': 'Grand Banquet Hall Bangalore',
                    'location_city': 'Bangalore',
                    'capacity': 200,
                    'rental_cost': 240000,
                    'contact_phone': '+91-80-12345678',
                    'contact_email': 'events@grandbanquet.com'
                },
                'caterer': {
                    'name': 'Royal South Indian Caterers',
                    'location_city': 'Bangalore',
                    'cost_per_person': 2133,
                    'total_cost': 320000,
                    'contact_phone': '+91-98765-43210',
                    'contact_email': 'bookings@royalcaterers.com'
                },
                'photographer': {
                    'name': 'Traditional Moments Photography',
                    'location_city': 'Bangalore',
                    'package_cost': 80000,
                    'contact_phone': '+91-99876-54321',
                    'contact_email': 'info@traditionalmoments.com'
                },
                'makeup_artist': {
                    'name': 'Bridal Beauty Experts',
                    'location_city': 'Bangalore',
                    'bridal_package_cost': 64000,
                    'contact_phone': '+91-98765-12345',
                    'contact_email': 'bookings@bridalbeauty.com'
                }
            },
            {
                'combination_id': 'combo_002',
                'fitness_score': 88.3,
                'total_cost': 720000,
                'venue': {
                    'name': 'Elegant Gardens Venue',
                    'location_city': 'Bangalore',
                    'capacity': 180,
                    'rental_cost': 220000
                },
                'caterer': {
                    'name': 'Heritage Catering Services',
                    'location_city': 'Bangalore',
                    'cost_per_person': 2000,
                    'total_cost': 300000
                },
                'photographer': {
                    'name': 'Classic Wedding Photography',
                    'location_city': 'Bangalore',
                    'package_cost': 85000
                },
                'makeup_artist': {
                    'name': 'Glamour Studio Bangalore',
                    'location_city': 'Bangalore',
                    'bridal_package_cost': 75000
                }
            }
        ]
    
    def create_demo_tasks(self) -> List[Dict]:
        """Create demo tasks"""
        event_date = datetime.fromisoformat(self.client_data.get('event_date'))
        
        return [
            {
                'id': 'task_001',
                'name': 'Venue booking and contract signing',
                'priority': 'Critical',
                'status': 'Completed',
                'duration': 120,
                'start_time': (event_date - timedelta(days=60)).isoformat(),
                'vendor': 'Grand Banquet Hall',
                'dependencies': []
            },
            {
                'id': 'task_002',
                'name': 'Catering menu finalization',
                'priority': 'Critical',
                'status': 'In Progress',
                'duration': 180,
                'start_time': (event_date - timedelta(days=45)).isoformat(),
                'vendor': 'Royal South Indian Caterers',
                'dependencies': ['task_001']
            },
            {
                'id': 'task_003',
                'name': 'Photography package booking',
                'priority': 'High',
                'status': 'In Progress',
                'duration': 90,
                'start_time': (event_date - timedelta(days=30)).isoformat(),
                'vendor': 'Traditional Moments Photography',
                'dependencies': []
            },
            {
                'id': 'task_004',
                'name': 'Makeup trial session',
                'priority': 'High',
                'status': 'Pending',
                'duration': 120,
                'start_time': (event_date - timedelta(days=21)).isoformat(),
                'vendor': 'Bridal Beauty Experts',
                'dependencies': []
            },
            {
                'id': 'task_005',
                'name': 'Venue decoration planning',
                'priority': 'Medium',
                'status': 'Pending',
                'duration': 240,
                'start_time': (event_date - timedelta(days=14)).isoformat(),
                'vendor': 'Grand Banquet Hall',
                'dependencies': ['task_001']
            },
            {
                'id': 'task_006',
                'name': 'Final guest count confirmation',
                'priority': 'Critical',
                'status': 'Pending',
                'duration': 60,
                'start_time': (event_date - timedelta(days=14)).isoformat(),
                'vendor': 'Client',
                'dependencies': []
            },
            {
                'id': 'task_007',
                'name': 'Catering final confirmation',
                'priority': 'Critical',
                'status': 'Pending',
                'duration': 90,
                'start_time': (event_date - timedelta(days=7)).isoformat(),
                'vendor': 'Royal South Indian Caterers',
                'dependencies': ['task_002', 'task_006']
            },
            {
                'id': 'task_008',
                'name': 'Venue setup and decoration',
                'priority': 'High',
                'status': 'Pending',
                'duration': 480,
                'start_time': (event_date - timedelta(hours=12)).isoformat(),
                'vendor': 'Grand Banquet Hall',
                'dependencies': ['task_005']
            },
            {
                'id': 'task_009',
                'name': 'Bridal makeup application',
                'priority': 'High',
                'status': 'Pending',
                'duration': 180,
                'start_time': event_date.replace(hour=8, minute=0).isoformat(),
                'vendor': 'Bridal Beauty Experts',
                'dependencies': ['task_004']
            },
            {
                'id': 'task_010',
                'name': 'Photography - Getting ready shots',
                'priority': 'Medium',
                'status': 'Pending',
                'duration': 120,
                'start_time': event_date.replace(hour=10, minute=0).isoformat(),
                'vendor': 'Traditional Moments Photography',
                'dependencies': ['task_009']
            },
            {
                'id': 'task_011',
                'name': 'Wedding ceremony',
                'priority': 'Critical',
                'status': 'Pending',
                'duration': 90,
                'start_time': event_date.replace(hour=18, minute=0).isoformat(),
                'vendor': 'Grand Banquet Hall',
                'dependencies': ['task_008', 'task_009']
            },
            {
                'id': 'task_012',
                'name': 'Reception and dinner service',
                'priority': 'Critical',
                'status': 'Pending',
                'duration': 240,
                'start_time': event_date.replace(hour=19, minute=30).isoformat(),
                'vendor': 'Royal South Indian Caterers',
                'dependencies': ['task_011']
            }
        ]
    
    # ==================== MAIN DEMO EXECUTION ====================
    
    def run_complete_demo(self) -> bool:
        """Run the complete platform demo"""
        self.print_header("COMPLETE EVENT MANAGEMENT PLATFORM DEMO", "=")
        
        intro_lines = [
            "🎯 This demo showcases the complete Event Planning Agent v2 platform:",
            "   � PaPrt 1: Event Planning - AI-powered vendor sourcing and optimization",
            "   � Part 2:3 CRM - Client communication preferences and tracking",
            "   📅 Part 3: Task Management - Task tracking, timeline, and conflict resolution",
            f"\n📁 Using client data from: {self.client_data_path}"
        ]
        for line in intro_lines:
            print(line)
        self.output_lines.extend(intro_lines)
        
        # Load client data
        if not self.load_client_data():
            print("\n❌ Demo cannot continue without client data")
            return False
        
        # Check API health (optional - will continue in demo mode if API is down)
        self.check_api_health()
        
        # Part 1: Event Planning
        try:
            if not self.demo_event_planning():
                print("\n⚠️ Event Planning phase had issues, continuing...")
        except Exception as e:
            print(f"\n⚠️ Event Planning error: {e}")
        
        # Part 2: CRM & Communications
        try:
            if not self.demo_crm_communications():
                print("\n⚠️ CRM phase had issues, continuing...")
        except Exception as e:
            print(f"\n⚠️ CRM error: {e}")
        
        # Part 3: Task Management
        try:
            if not self.demo_task_management():
                print("\n⚠️ Task Management phase had issues, continuing...")
        except Exception as e:
            print(f"\n⚠️ Task Management error: {e}")
        
        # Final Summary
        self.print_final_summary()
        
        # Save output to file
        self.save_output_to_file()
        
        return True
    
    def print_final_summary(self):
        """Print final demo summary"""
        self.print_header("DEMO COMPLETED SUCCESSFULLY! 🎉", "=")
        
        lines = [
            "\n✅ All platform features demonstrated:",
            "\n📋 EVENT PLANNING:",
            "   ✓ Client requirements processing",
            "   ✓ AI-powered vendor sourcing",
            "   ✓ Multi-agent workflow coordination",
            "   ✓ Intelligent combination optimization",
            "   ✓ Fitness scoring and ranking",
            "   ✓ Comprehensive blueprint generation",
            "   ✓ Multi-format export capabilities",
            "\n💬 CRM & COMMUNICATIONS:",
            "   ✓ Communication preference management",
            "   ✓ Multi-channel support (Email, SMS, WhatsApp)",
            "   ✓ Timezone and quiet hours configuration",
            "   ✓ Communication history tracking",
            "   ✓ Delivery and engagement monitoring",
            "   ✓ Analytics and performance metrics",
            "   ✓ Channel effectiveness analysis",
            "\n📅 TASK MANAGEMENT:",
            "   ✓ Extended task list with dependencies",
            "   ✓ Priority-based task organization",
            "   ✓ Timeline visualization (Gantt chart)",
            "   ✓ Conflict detection and resolution",
            "   ✓ Vendor assignment tracking",
            "   ✓ Workload distribution analysis",
            "   ✓ Progress monitoring and reporting",
            f"\n🎊 Event Details:",
            f"   Client: {self.client_data.get('client_name')}",
            f"   Event: {self.client_data.get('event_type')}",
            f"   Date: {self.client_data.get('event_date')}",
            f"   Location: {self.client_data.get('location')}",
            f"   Guests: {self.client_data.get('total_guests')}",
            f"   Budget: ₹{self.client_data.get('total_budget', 0):,.0f}",
            f"   Theme: {self.client_data.get('event_theme')}",
            f"\n📊 Platform Capabilities:",
            f"   • End-to-end event planning automation",
            f"   • Real-time client communication management",
            f"   • Comprehensive task and vendor coordination",
            f"   • AI-powered optimization and recommendations",
            f"   • Multi-channel engagement tracking",
            f"   • Conflict detection and resolution",
            f"   • Progress monitoring and analytics",
            f"\n💡 Next Steps:",
            f"   1. Review the generated blueprint and task list",
            f"   2. Confirm vendor selections and bookings",
            f"   3. Monitor task progress and resolve conflicts",
            f"   4. Track client communications and engagement",
            f"   5. Use analytics to optimize event planning",
            f"\n🚀 The complete Event Management Platform is ready!",
            "=" * 80
        ]
        
        for line in lines:
            print(line)
        self.output_lines.extend(lines)
    
    def save_output_to_file(self):
        """Save demo output to text file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"demo_output_{timestamp}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("EVENT MANAGEMENT PLATFORM - COMPLETE DEMO OUTPUT\n")
                f.write("=" * 80 + "\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 80 + "\n\n")
                
                for line in self.output_lines:
                    f.write(line + "\n")
                
                f.write("\n" + "=" * 80 + "\n")
                f.write("END OF DEMO OUTPUT\n")
                f.write("=" * 80 + "\n")
            
            print(f"\n📄 Demo output saved to: {filename}")
            self.output_lines.append(f"\n📄 Demo output saved to: {filename}")
            return filename
        except Exception as e:
            print(f"\n⚠️ Failed to save output file: {e}")
            return None


def main():
    """Main function to run the demo"""
    try:
        # You can specify a different client data file path if needed
        demo = CompleteEventManagementDemo("streamlit_gui/client_data.json")
        
        success = demo.run_complete_demo()
        
        if success:
            print("\n🌟 Demo completed successfully!")
            print("📁 Check the generated files for detailed event plan")
            print("💡 Run the Streamlit GUI to explore the full platform interactively")
            print("   Command: streamlit run streamlit_gui/app.py")
        else:
            print("\n⚠️ Demo completed with some issues")
            print("💡 Check the output above for details")
        
        return success
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Demo interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
