from flask import Flask, render_template, request, jsonify
import random
import time
from datetime import datetime

app = Flask(__name__)

# Loan approval criteria
APPROVAL_CRITERIA = {
    'excellent': {'min_income_multiplier': 0.1, 'approval_rate': 0.95},
    'good': {'min_income_multiplier': 0.15, 'approval_rate': 0.80},
    'fair': {'min_income_multiplier': 0.25, 'approval_rate': 0.50},
    'poor': {'min_income_multiplier': 0.40, 'approval_rate': 0.20}
}

# Employment multipliers
EMPLOYMENT_MULTIPLIERS = {
    'employed': 1.0,
    'self-employed': 1.2,
    'unemployed': 2.0,
    'student': 1.5
}

def calculate_loan_eligibility(income, loan_amount, credit_score, employment):
    """
    Calculate loan eligibility based on multiple factors
    """
    try:
        # Get base criteria for credit score
        base_criteria = APPROVAL_CRITERIA.get(credit_score, APPROVAL_CRITERIA['poor'])
        
        # Calculate minimum required income
        min_income = loan_amount * base_criteria['min_income_multiplier']
        
        # Apply employment multiplier
        employment_multiplier = EMPLOYMENT_MULTIPLIERS.get(employment, 2.0)
        adjusted_min_income = min_income * employment_multiplier
        
        # Check if income meets minimum requirement
        income_adequate = income >= adjusted_min_income
        
        # Generate approval probability
        base_approval_rate = base_criteria['approval_rate']
        
        # Adjust approval rate based on income adequacy
        if income_adequate:
            approval_rate = base_approval_rate
        else:
            approval_rate = base_approval_rate * 0.3  # Reduce approval rate if income inadequate
        
        # Add some randomness to make it more realistic
        final_approval_rate = max(0.05, min(0.95, approval_rate + random.uniform(-0.1, 0.1)))
        
        # Determine approval
        approved = random.random() < final_approval_rate
        
        # Generate appropriate interest rate
        if approved:
            base_rate = 5.0  # Base interest rate
            credit_adjustment = {'excellent': -2.0, 'good': 0.0, 'fair': 2.0, 'poor': 4.0}
            employment_adjustment = {'employed': 0.0, 'self-employed': 0.5, 'unemployed': 2.0, 'student': 1.0}
            
            interest_rate = (base_rate + 
                           credit_adjustment.get(credit_score, 4.0) + 
                           employment_adjustment.get(employment, 2.0) + 
                           random.uniform(-0.5, 0.5))
            
            interest_rate = max(3.0, min(15.0, interest_rate))
        else:
            interest_rate = None
        
        return {
            'approved': approved,
            'interest_rate': round(interest_rate, 2) if interest_rate else None,
            'monthly_payment': calculate_monthly_payment(loan_amount, interest_rate) if approved else None,
            'reason': generate_approval_reason(approved, income, adjusted_min_income, credit_score, employment)
        }
        
    except Exception as e:
        return {
            'approved': False,
            'interest_rate': None,
            'monthly_payment': None,
            'reason': 'System error during evaluation'
        }

def calculate_monthly_payment(loan_amount, annual_rate, years=5):
    """Calculate monthly loan payment"""
    if not annual_rate:
        return None
    
    monthly_rate = annual_rate / 100 / 12
    num_payments = years * 12
    
    if monthly_rate == 0:
        return loan_amount / num_payments
    
    monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
    return round(monthly_payment, 2)

def generate_approval_reason(approved, income, min_income, credit_score, employment):
    """Generate appropriate approval/rejection reason"""
    if approved:
        reasons = [
            "Your application meets our lending criteria.",
            "Congratulations! You qualify for this loan amount.",
            "Based on your financial profile, you are approved.",
            "Your strong credit history and income qualify you for this loan."
        ]
        return random.choice(reasons)
    else:
        if income < min_income:
            return "Your current income does not meet our minimum requirements for this loan amount."
        elif credit_score == 'poor':
            return "Your credit score does not currently meet our lending criteria."
        elif employment == 'unemployed':
            return "We require stable employment for loan approval."
        else:
            return "Based on our current lending criteria, we cannot approve your application at this time."

@app.route('/')
def index():
    """Serve the main loan application page"""
    return render_template('index.html')

@app.route('/api/apply-loan', methods=['POST'])
def apply_loan():
    """Handle loan application submission"""
    try:
        # Get form data
        data = request.get_json()
        
        # Extract application details
        full_name = data.get('fullName', '')
        email = data.get('email', '')
        phone = data.get('phone', '')
        income = float(data.get('income', 0))
        loan_amount = float(data.get('loanAmount', 0))
        credit_score = data.get('creditScore', 'poor')
        employment = data.get('employment', 'unemployed')
        
        # Simulate processing time
        time.sleep(2)
        
        # Calculate eligibility
        result = calculate_loan_eligibility(income, loan_amount, credit_score, employment)
        
        # Create response
        response = {
            'success': True,
            'application_id': f"APP{int(time.time())}",
            'timestamp': datetime.now().isoformat(),
            'applicant_name': full_name,
            'loan_amount': loan_amount,
            'approved': result['approved'],
            'interest_rate': result['interest_rate'],
            'monthly_payment': result['monthly_payment'],
            'message': result['reason'],
            'details': generate_detailed_response(result['approved'], loan_amount, result['interest_rate'], result['monthly_payment'])
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'An error occurred while processing your application.'
        }), 500

def generate_detailed_response(approved, loan_amount, interest_rate, monthly_payment):
    """Generate detailed response message"""
    if approved:
        return f"You have been approved for a ${loan_amount:,.2f} loan at {interest_rate}% APR. Your estimated monthly payment will be ${monthly_payment:,.2f} over 5 years."
    else:
        return "We encourage you to improve your credit score or consider a smaller loan amount. You may reapply after 6 months."

@app.route('/api/loan-status/<application_id>')
def loan_status(application_id):
    """Check loan application status"""
    # This would typically query a database
    # For demo purposes, return a mock response
    return jsonify({
        'application_id': application_id,
        'status': 'processed',
        'decision': 'approved',
        'timestamp': datetime.now().isoformat()
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print("🚀 Starting Bank Loan Approval System...")
    print("📍 Server will be available at: http://localhost:5000")
    print("🔧 Debug mode enabled for development")
    
    app.run(debug=True, host='0.0.0.0', port=5000)