# 🤝 Contributing to Novaryo Travel Platform

## ⚖️ **Important Legal Notice**

**This project is proprietary software owned by Aniket Kumar.**

Before contributing to this project, you **MUST**:
1. 📧 **Contact the owner:** aniket.kumar.devpro@gmail.com
2. 📱 **WhatsApp:** +91 8318601925  
3. ✍️ **Obtain written permission** for any contributions
4. 📋 **Sign a Contributor License Agreement (CLA)** if required

**⚠️ Unauthorized contributions may not be accepted and could result in legal complications.**

---

## 🚀 Getting Started (After Authorization)

### Prerequisites
- Python 3.13+
- PostgreSQL (optional)
- Redis
- Git knowledge
- Django experience

### Development Setup

1. **Get Permission First**
   ```bash
   # Contact aniket.kumar.devpro@gmail.com before proceeding
   ```

2. **Fork the Repository** (after authorization)
   ```bash
   git clone https://github.com/yourusername/novaryo.git
   cd novaryo
   ```

3. **Set up Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Database Setup**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

5. **Run Development Server**
   ```bash
   python manage.py runserver
   ```

---

## 🎯 How to Contribute (After Authorization)

### 🐛 **Bug Reports**
- 🔍 Search existing issues first
- 📝 Use the bug report template
- 🖼️ Include screenshots if applicable
- 🔄 Provide reproduction steps
- 💻 Include system information

### 💡 **Feature Requests**
- 💭 Check if feature aligns with project goals
- 📋 Use the feature request template
- 🎨 Include mockups if UI-related
- 📊 Explain business value
- 🔧 Consider implementation complexity

### 🔧 **Code Contributions**

#### **Coding Standards**
```python
# Follow PEP 8 guidelines
# Use descriptive variable names
# Add docstrings to functions and classes
# Write unit tests for new features

def calculate_booking_total(base_price, taxes, fees):
    """
    Calculate total booking price including taxes and fees.
    
    Args:
        base_price (Decimal): Base booking price
        taxes (Decimal): Tax amount
        fees (Decimal): Additional fees
        
    Returns:
        Decimal: Total booking amount
    """
    return base_price + taxes + fees
```

#### **Commit Message Format**
```
feat: add hotel availability search
fix: resolve payment calculation bug
docs: update API documentation
style: format booking forms
refactor: optimize database queries
test: add loyalty program tests
```

#### **Branch Naming**
```
feature/hotel-search-filters
bugfix/payment-calculation-error
hotfix/security-vulnerability
docs/api-documentation-update
```

---

## 🧪 Testing Guidelines

### **Run Tests**
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test hotels
python manage.py test bookings

# Run with coverage
coverage run manage.py test
coverage report
```

### **Writing Tests**
- 📝 Write unit tests for models
- 🌐 Write integration tests for views
- 🔌 Write API endpoint tests
- 🎯 Aim for 80%+ test coverage
- 🚀 Test edge cases and error conditions

---

## 📚 Documentation

### **Code Documentation**
- 📖 Document all public functions
- 📝 Add inline comments for complex logic
- 🔄 Update docstrings when modifying functions
- 📋 Include examples in docstrings

### **API Documentation**
- 🔧 Update Swagger documentation
- 📊 Include request/response examples
- ⚠️ Document error responses
- 🔒 Document authentication requirements

---

## 🔍 Code Review Process

### **Before Submitting PR**
- ✅ All tests pass
- 📏 Code follows style guidelines
- 📝 Documentation is updated
- 🐛 No new security vulnerabilities
- 📊 Performance impact considered

### **PR Requirements**
- 📋 Clear description of changes
- 🔗 Link to related issue
- 🧪 Test results included
- 📸 Screenshots for UI changes
- 📝 Migration files if database changes

### **Review Criteria**
- 🎯 **Functionality** - Does it work as expected?
- 🏗️ **Architecture** - Follows Django best practices?
- 🔒 **Security** - No security vulnerabilities?
- ⚡ **Performance** - Doesn't degrade performance?
- 📚 **Documentation** - Adequately documented?

---

## 🏗️ Development Workflow

1. 📧 **Get Authorization** from project owner
2. 🍴 **Fork** the repository
3. 🌿 **Create** feature branch from `develop`
4. 💻 **Develop** your feature/fix
5. 🧪 **Test** thoroughly
6. 📝 **Document** your changes
7. 🔄 **Submit** pull request
8. 👥 **Respond** to code review feedback
9. ✅ **Merge** after approval

---

## 🎨 UI/UX Contributions

### **Design Guidelines**
- 🎨 Follow Novaryo brand colors
- 📱 Ensure mobile responsiveness
- ♿ Maintain accessibility standards
- 🔄 Use consistent component patterns
- ⚡ Optimize for performance

### **Brand Colors**
```css
--novaryo-primary: #2c5282;
--novaryo-secondary: #3182ce;
--novaryo-accent: #ed8936;
--novaryo-light: #f7fafc;
--novaryo-dark: #2d3748;
```

---

## 📊 Performance Guidelines

- ⚡ Database queries should be optimized
- 🗃️ Use select_related and prefetch_related
- 💾 Implement proper caching strategies
- 📱 Ensure mobile performance
- 🔍 Profile code before and after changes

---

## 🔒 Security Considerations

- 🛡️ Never commit sensitive data
- 🔐 Validate all user inputs
- 🚫 Use Django's built-in security features
- 🔒 Follow OWASP guidelines
- 🔍 Run security scans regularly

---

## 📞 Support & Questions

**Primary Contact:**
- 👨‍💻 **Developer:** Aniket Kumar
- 📧 **Email:** aniket.kumar.devpro@gmail.com
- 📱 **WhatsApp:** +91 8318601925
- 🐙 **GitHub:** @Aniket-Dev-IT

**Response Time:** 24-48 hours during business days

---

## 🏷️ Issue Labels

- 🐛 `bug` - Something isn't working
- 💡 `enhancement` - New feature or request
- 📚 `documentation` - Documentation improvements
- 🆘 `help-wanted` - Extra attention needed
- 🚨 `priority-high` - High priority issue
- 🔒 `security` - Security related
- 🧪 `testing` - Testing related
- 🎨 `ui/ux` - User interface/experience

---

## ⚖️ **Final Legal Reminder**

This project is **proprietary software**. All contributions become part of the proprietary codebase owned by Aniket Kumar. 

**Contributors must:**
- ✍️ Have written authorization to contribute
- 📋 May need to sign a CLA
- 🔒 Respect intellectual property rights
- 📧 Contact owner before any contributions

**© 2025 Aniket Kumar - All Rights Reserved**

---

Thank you for your interest in contributing to Novaryo! 🚀✨