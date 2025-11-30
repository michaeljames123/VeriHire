# 🔍 VeriHire

## Overview 📖

This project leverages Natural Language Processing (NLP) and Machine Learning to detect fraudulent job postings. The system processes job posting data, extracts relevant features, and classifies the postings as either fraudulent or legitimate.

## ⚙️ Tech Stack

- Python
- Flask
- HTML/CSS
- scikit-learn
- pandas
- nltk

## Features ✨

- **Data Preprocessing**: Cleans and preprocesses job posting data for analysis.
- **Feature Extraction**: Utilizes NLP techniques to extract features from text data.
- **Model Training**: Implements machine learning algorithms to classify job postings.
- **Web Interface**: Provides a user-friendly interface for interacting with the classifier.

## Requirements 🛠️

- Python 3.9
- Flask

## Installation 📦

1. Create and Activate Virtual Environment
   ```sh
   py -3.9 -m venv venv
   ```

3. Clone the repository:

   ```sh
   git clone https://github.com/PowerHouseBSIT/VeriHire.git verihire
   cd VeriHire
   ```

4. Install the required packages:

   ```sh
   pip install -r requirements.txt
   ```

5. Run the model.py to preprocess the data and train the model:
   ```sh
   py model.py
   ```

## Usage 🚀

1. **Run the Flask application**:

   ```sh
   python app.py
   ```

2. **Access the web interface**:

   - Open your browser and go to `http://localhost:5000`.

3. **Classify Job Postings**:
   - Use the web interface to input job postings and receive classification results.

## File Structure 🗂️

- `app.py`: Flask application script.
- `static/`: Static assets like CSS and images.
- `templates/`: HTML templates for the web interface.
- `model.py`: Script for building and evaluating the machine learning model.
- `requirements.txt`: List of required Python packages.
