import os
import random
from datetime import datetime, timedelta
import pandas as pd
from generators.base import BaseGenerator

class EmployeesGenerator(BaseGenerator):
    def generate(self, output_dir):
        random.seed(self.seed)
        
        num_employees = self.config["sizes"]["employees"]
        
        # Load companies
        companies_path = os.path.join(output_dir, "master", "companies.csv")
        companies_df = pd.read_csv(companies_path)
        company_ids = companies_df["CompanyID"].tolist()
        
        departments = ["Procurement", "Logistics", "Operations", "Sales", "Finance", "HR", "ESG & Compliance", "Engineering"]
        designations = {
            "Procurement": ["Buyer", "Purchasing Manager", "Procurement Specialist", "VP of Supply Chain"],
            "Logistics": ["Logistics Analyst", "Fleet Coordinator", "Dispatcher", "Logistics Director"],
            "Operations": ["Plant operator", "Shift Supervisor", "Operations Engineer", "Plant Manager"],
            "Sales": ["Sales Representative", "Account Executive", "Sales Manager", "VP of Sales"],
            "Finance": ["Accountant", "Finance Manager", "Financial Analyst", "CFO"],
            "HR": ["HR Coordinator", "HR Recruiter", "HR Manager", "VP of HR"],
            "ESG & Compliance": ["ESG Analyst", "Sustainability Specialist", "EHS Manager", "Chief Sustainability Officer"],
            "Engineering": ["Junior Engineer", "Lead Developer", "R&D Specialist", "VP of Engineering"]
        }
        
        grades = ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5"]
        travel_categories = ["Economy", "Economy", "Economy", "Business", "First Class"] # Map directly to Grade indices
        
        employees = []
        company_employees = {cid: [] for cid in company_ids}
        
        for i in range(num_employees):
            emp_id = i + 1
            company_id = random.choice(company_ids)
            
            dept = random.choice(departments)
            desig_list = designations[dept]
            
            # Simple seniority logic
            grade_idx = random.randint(0, 4)
            grade = grades[grade_idx]
            travel_cat = travel_categories[grade_idx]
            desig = desig_list[min(grade_idx, len(desig_list) - 1)]
            
            salary = round(random.uniform(30000.0 + (grade_idx * 20000.0), 60000.0 + (grade_idx * 40000.0)), 2)
            
            # Determine Manager
            manager_id = None
            if len(company_employees[company_id]) > 0:
                # 70% chance to have a manager from previous employees in same company
                if random.random() < 0.7:
                    manager_id = random.choice(company_employees[company_id])
            
            # Joining date between 2018 and 2023
            joining_days = random.randint(0, 1800)
            joining_date = (datetime(2018, 1, 1) + timedelta(days=joining_days)).strftime("%Y-%m-%d")
            status = random.choice(["Active", "Active", "Active", "Resigned"])
            
            employees.append({
                "EmployeeID": emp_id,
                "CompanyID": company_id,
                "Department": dept,
                "Designation": desig,
                "ManagerID": manager_id,
                "Salary": salary,
                "Grade": grade,
                "TravelCategory": travel_cat,
                "JoiningDate": joining_date,
                "Status": status
            })
            
            # Cache employee ID for manager references
            company_employees[company_id].append(emp_id)
            
        df = pd.DataFrame(employees)
        self.save_data(df, output_dir, "employees", is_master=True, pk_col="EmployeeID")
        print(f"Generated {num_employees} Employees.")
