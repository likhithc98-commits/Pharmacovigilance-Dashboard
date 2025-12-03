# Pharmacovigilance Data Dashboard
# SQL-based Data Pipeline + Visualization Dashboard
# Tracks patient medication adherence trends for digital intervention planning

import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class PharmacovgilanceDashboard:
    def __init__(self, db_path='pharmacovigilance.db'):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
    def initialize_database(self):
        """Create SQLite database with pharmacovigilance schema"""
        print("[INFO] Initializing Pharmacovigilance Database...")
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # Patients table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                patient_id INTEGER PRIMARY KEY,
                age INTEGER,
                gender TEXT,
                chronic_condition TEXT,
                registration_date DATE
            )
        ''')
        
        # Medications table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS medications (
                medication_id INTEGER PRIMARY KEY,
                patient_id INTEGER,
                drug_name TEXT,
                prescribed_date DATE,
                dosage TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
            )
        ''')
        
        # Adherence tracking table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS adherence (
                adherence_id INTEGER PRIMARY KEY,
                patient_id INTEGER,
                medication_id INTEGER,
                adherence_date DATE,
                doses_taken INTEGER,
                doses_prescribed INTEGER,
                adherence_percentage REAL,
                FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
                FOREIGN KEY (medication_id) REFERENCES medications(medication_id)
            )
        ''')
        
        self.conn.commit()
        print("[SUCCESS] Database initialized with pharmacovigilance schema")
        
    def populate_synthetic_data(self, n_patients=500):
        """Generate realistic synthetic patient adherence data"""
        print(f"\n[INFO] Generating synthetic adherence data for {n_patients} patients...")
        
        np.random.seed(42)
        base_date = datetime(2024, 1, 1)
        
        # Insert patients
        for i in range(1, n_patients + 1):
            age = np.random.randint(18, 80)
            gender = np.random.choice(['M', 'F'])
            condition = np.random.choice(['Hypertension', 'Diabetes', 'Heart Disease', 'Asthma'])
            reg_date = (base_date + timedelta(days=np.random.randint(0, 365))).date()
            
            self.cursor.execute('''
                INSERT INTO patients (patient_id, age, gender, chronic_condition, registration_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (i, age, gender, condition, reg_date))
        
        # Insert medications and adherence data
        med_id = 1
        drugs = ['Lisinopril', 'Metformin', 'Atorvastatin', 'Amlodipine', 'Albuterol']
        
        for patient_id in range(1, n_patients + 1):
            num_meds = np.random.randint(1, 4)
            for _ in range(num_meds):
                drug = np.random.choice(drugs)
                prescribed_date = (base_date + timedelta(days=np.random.randint(0, 300))).date()
                
                self.cursor.execute('''
                    INSERT INTO medications (medication_id, patient_id, drug_name, prescribed_date, dosage)
                    VALUES (?, ?, ?, ?, ?)
                ''', (med_id, patient_id, drug, prescribed_date, '1 tablet daily'))
                
                # Add adherence records for 30 days
                for day in range(30):
                    adherence_date = prescribed_date + timedelta(days=day)
                    doses_prescribed = 1
                    doses_taken = np.random.choice([0, 1, 1, 1])  # 75% adherence on average
                    adherence_pct = (doses_taken / doses_prescribed * 100) if doses_prescribed > 0 else 0
                    
                    self.cursor.execute('''
                        INSERT INTO adherence (patient_id, medication_id, adherence_date, 
                                             doses_taken, doses_prescribed, adherence_percentage)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (patient_id, med_id, adherence_date, doses_taken, doses_prescribed, adherence_pct))
                
                med_id += 1
        
        self.conn.commit()
        print(f"[SUCCESS] Generated synthetic data: {n_patients} patients with medication records")
        
    def analyze_adherence_trends(self):
        """SQL query to analyze patient adherence trends"""
        print("\n[ANALYSIS] Patient Adherence Trends")
        
        query = '''
            SELECT 
                p.patient_id,
                p.age,
                p.chronic_condition,
                AVG(a.adherence_percentage) as avg_adherence,
                COUNT(DISTINCT a.medication_id) as num_medications,
                CASE 
                    WHEN AVG(a.adherence_percentage) >= 90 THEN 'Excellent'
                    WHEN AVG(a.adherence_percentage) >= 75 THEN 'Good'
                    WHEN AVG(a.adherence_percentage) >= 50 THEN 'Fair'
                    ELSE 'Poor'
                END as adherence_category
            FROM patients p
            LEFT JOIN adherence a ON p.patient_id = a.patient_id
            GROUP BY p.patient_id
            ORDER BY avg_adherence DESC
        '''
        
        df = pd.read_sql_query(query, self.conn)
        print("\nTop 10 Compliant Patients (High Adherence):")
        print(df.head(10).to_string(index=False))
        
        # Adherence distribution
        adherence_dist = df['adherence_category'].value_counts()
        print("\nAdherence Category Distribution:")
        for cat, count in adherence_dist.items():
            pct = (count / len(df)) * 100
            print(f"  {cat}: {count} patients ({pct:.1f}%)")
        
        return df
    
    def identify_intervention_candidates(self):
        """Identify patients needing digital intervention (poor adherence)"""
        print("\n[INTERVENTION] Patients Requiring Digital Intervention")
        
        query = '''
            SELECT 
                p.patient_id,
                p.age,
                p.chronic_condition,
                AVG(a.adherence_percentage) as avg_adherence,
                COUNT(DISTINCT a.medication_id) as num_medications
            FROM patients p
            LEFT JOIN adherence a ON p.patient_id = a.patient_id
            GROUP BY p.patient_id
            HAVING AVG(a.adherence_percentage) < 75
            ORDER BY avg_adherence ASC
            LIMIT 20
        '''
        
        df = pd.read_sql_query(query, self.conn)
        print(f"\nIdentified {len(df)} patients with poor adherence (<75%)")
        print("\nTop Intervention Candidates:")
        print(df.to_string(index=False))
        
        return df
    
    def visualize_adherence_dashboard(self):
        """Create adherence visualizations"""
        print("\n[VISUALIZATION] Generating Dashboard Charts...")
        
        # Fetch data
        query_adherence = '''
            SELECT 
                p.chronic_condition,
                AVG(a.adherence_percentage) as avg_adherence
            FROM patients p
            LEFT JOIN adherence a ON p.patient_id = a.patient_id
            GROUP BY p.chronic_condition
        '''
        
        df_adherence = pd.read_sql_query(query_adherence, self.conn)
        
        # Create visualizations
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Pharmacovigilance Dashboard - Patient Adherence Analytics', fontsize=16, fontweight='bold')
        
        # Chart 1: Adherence by Condition
        axes[0, 0].bar(df_adherence['chronic_condition'], df_adherence['avg_adherence'], color='steelblue')
        axes[0, 0].set_title('Average Adherence by Chronic Condition')
        axes[0, 0].set_ylabel('Adherence %')
        axes[0, 0].set_ylim(0, 100)
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # Chart 2: Patient Age Distribution
        query_age = 'SELECT age FROM patients'
        df_age = pd.read_sql_query(query_age, self.conn)
        axes[0, 1].hist(df_age['age'], bins=20, color='coral', edgecolor='black')
        axes[0, 1].set_title('Patient Age Distribution')
        axes[0, 1].set_xlabel('Age (years)')
        axes[0, 1].set_ylabel('Number of Patients')
        
        # Chart 3: Adherence Distribution (Pie)
        query_dist = '''
            SELECT 
                CASE 
                    WHEN AVG(adherence_percentage) >= 90 THEN 'Excellent (>90%)'
                    WHEN AVG(adherence_percentage) >= 75 THEN 'Good (75-90%)'
                    ELSE 'Poor (<75%)'
                END as category,
                COUNT(*) as count
            FROM (SELECT patient_id, AVG(adherence_percentage) as adherence_percentage 
                  FROM adherence GROUP BY patient_id)
            GROUP BY category
        '''
        df_dist = pd.read_sql_query(query_dist, self.conn)
        axes[1, 0].pie(df_dist['count'], labels=df_dist['category'], autopct='%1.1f%%', colors=['green', 'yellow', 'red'])
        axes[1, 0].set_title('Patient Adherence Levels')
        
        # Chart 4: Medication Distribution
        query_meds = '''
            SELECT drug_name, COUNT(*) as count
            FROM medications
            GROUP BY drug_name
        '''
        df_meds = pd.read_sql_query(query_meds, self.conn)
        axes[1, 1].barh(df_meds['drug_name'], df_meds['count'], color='lightgreen')
        axes[1, 1].set_title('Medication Distribution')
        axes[1, 1].set_xlabel('Number of Prescriptions')
        
        plt.tight_layout()
        plt.show()
        print("[SUCCESS] Dashboard visualizations generated")
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

def main():
    print("\n" + "="*70)
    print(" PHARMACOVIGILANCE DATA DASHBOARD")
    print(" SQL-Based Data Pipeline & Adherence Monitoring")
    print("="*70)
    
    dashboard = PharmacovgilanceDashboard()
    
    # Initialize and populate
    dashboard.initialize_database()
    dashboard.populate_synthetic_data(n_patients=500)
    
    # Analysis
    adherence_df = dashboard.analyze_adherence_trends()
    intervention_df = dashboard.identify_intervention_candidates()
    
    # Visualization
    dashboard.visualize_adherence_dashboard()
    
    # Summary
    print("\n" + "="*70)
    print("[SUMMARY] Dashboard Insights:")
    print(f"  - Total Patients Analyzed: {len(adherence_df)}")
    print(f"  - Patients Needing Intervention: {len(intervention_df)}")
    print(f"  - Average System Adherence: {adherence_df['avg_adherence'].mean():.1f}%")
    print("="*70 + "\n")
    
    dashboard.close()

if __name__ == "__main__":
    main()
