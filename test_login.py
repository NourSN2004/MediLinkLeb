"""Test login flows for all user types"""
import requests

def test_login(email, password, role):
    session = requests.Session()
    
    # Get CSRF token first
    get_resp = session.get('http://localhost:8080/')
    
    # Login
    login_resp = session.post('http://localhost:8080/login/', data={
        'username': email,
        'password': password
    }, allow_redirects=False)
    
    print(f"\n{'='*60}")
    print(f"Testing {role.upper()} Login: {email}")
    print(f"{'='*60}")
    print(f"Login Status: {login_resp.status_code}")
    
    if 'Location' in login_resp.headers:
        print(f"Redirect: {login_resp.headers['Location']}")
        
        # Follow redirect
        redirect_url = login_resp.headers['Location']
        if redirect_url.startswith('/'):
            redirect_url = 'http://localhost:8080' + redirect_url
        
        home_resp = session.get(redirect_url, allow_redirects=True)
        print(f"Home Page Status: {home_resp.status_code}")
        
        if home_resp.status_code == 200:
            print(f"✓ {role} home page loads successfully")
            # Check for static files
            if 'static/css/styles.css' in home_resp.text or '<style>' in home_resp.text:
                print(f"✓ CSS/Styles found in page")
            else:
                print(f"✗ CSS/Styles missing from page")
        else:
            print(f"✗ {role} home page failed")
            print(f"Response snippet: {home_resp.text[:500]}")
    else:
        print(f"✗ No redirect - login may have failed")
        print(f"Response: {login_resp.text[:500]}")
    
    return session

if __name__ == '__main__':
    # Test all user types
    test_login('doctor1@medilink.com', 'Password123!', 'doctor')
    test_login('patient1@medilink.com', 'Password123!', 'patient')
    test_login('pharmacy1@medilink.com', 'Password123!', 'pharmacy')
