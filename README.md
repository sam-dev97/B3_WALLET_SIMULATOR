# B3_WALLET_SIMULATOR
This is a Django-based stock trading application that allows users to buy and sell stocks, track their portfolio, and view their transaction history.

# Stock Trading Application
## Features

- User registration and authentication
- Add funds to user account
- Buy and sell stocks
- View real-time stock prices
- View transaction history

## Requirements

- Python 3.x
- Django 3.x
- yfinance
- Other dependencies listed in `requirements.txt`

## Installation

1. Clone the repository:

```sh
git clone https://github.com/your-username/your-repository.git
cd your-repository´
```

2. Create a virtual environment and activate it:
```sh
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate
```

3. Install the required dependencies:
```sh
pip install -r requirements.txt
```

4. Set up the database:
```sh
python manage.py migrate
```

5. Create a superuser
```sh
python manage.py createsuperuser
```

6. Run the development server:
```sh
python manage.py runserver
```

## Usage
Open your web browser and go to http://127.0.0.1:8000/.<br>
Register a new user or log in with the superuser account.<br>
Add funds to your account.<br>
Start buying and selling stocks.<br>

## Project Structure
manage.py: Django's command-line utility. <br>
requirements.txt: List of dependencies. <br>
app_wallet/: Contains the Django application code. <br>
models.py: Defines the database models. <br>
views.py: Contains the view functions. <br>
forms.py: Defines the forms used in the application. <br>
urls.py: URL routing for the application. <br>
templates/: HTML templates for the application. <br>
static/: Static files (CSS). <br>

## Contributing
Contributions are welcome! Please follow these steps:

Fork the repository.<br>
Create a new branch (git checkout -b feature-branch).<br>
Make your changes.<br>
Commit your changes (git commit -m 'Add some feature').<br>
Push to the branch (git push origin feature-branch).<br>
Open a pull request.<br>

## Acknowledgements
Django - The web framework used.<br>
yfinance - Library for accessing financial data.<br>
