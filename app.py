from flask import Flask, request, jsonify, render_template
from ast import literal_eval
from pymongo import MongoClient
from flask_cors import CORS
from dotenv import load_dotenv
load_dotenv()
import json
# from gemini.api import GeminiAPI
import google.generativeai as genai
# import torch
import os
# from pyresparser import resume_parser
JSON_FILE_PATH = 'database/resume_data.json'

# Load existing data from the JSON file
# try:
#     with open(JSON_FILE_PATH, 'r') as file:
#         resume_data = json.load(file)
# except FileNotFoundError:
#     # If the file doesn't exist, initialize an empty list
#     resume_data = []



app = Flask(__name__)

cors = CORS(app, resources={r"/*": {"origins": "*"}})
client=MongoClient(os.getenv('MONGO_URL'))
db=client.get_database('manit')
resume_data = list(db.resume.find())
# print(resume_data)

# @app.route('/opportunity', methods=['GET', 'POST'])
# def create_opportunity():
#     OPPORTUNITY_JSON_FILE = 'database/opportunity_data.json'
#     try:
#         with open(OPPORTUNITY_JSON_FILE, 'r') as file:
#             oppor_file = json.load(file)
#     except FileNotFoundError:
#     # If the file doesn't exist, initialize an empty list
#         oppor_file = []
#     if request.method == 'POST':
#         try:
#             data = request.json  # Assuming data is sent as JSON

#         # Append the new data to the existing list
#             oppor_file.append(data)

#         # Save the updated data back to the JSON file
#             with open(OPPORTUNITY_JSON_FILE, 'w') as file:
#                 json.dump(oppor_file, file, indent=4)

#             return jsonify({'message': 'opportunity submitted successfully'}), 200
#         except Exception as e:
#             return jsonify({'error': str(e)}), 500
#     return jsonify(oppor_file),200

#   <-----opportunity---->

@app.route('/opportunity', methods=['GET', 'POST'])
def create_opportunity():
    
    if request.method == 'POST':
        user_input = request.data
        user_input=literal_eval(user_input.decode('utf-8'))
        # user_input=json.loads(user_input["user"])
        
        try:
           db.opportunity.insert_one({"title":user_input["title"],"description":user_input["description"], "location":user_input["location"],"deadline":user_input["deadline"]})
        except Exception as e:
            return "Error in db"
        return jsonify({'message': 'opportunity saved successfully'}), 200
    data = jsonify(list(db.opportunity.find({}, {'_id': 0})))
    print(data)
    return data, 200

genai.configure(api_key=os.getenv('API_KEY'))

# Load Gemini Pro model
model = genai.GenerativeModel("gemini-pro") 
chat = model.start_chat(history=[])
def get_gemini_response(question):
    response = chat.send_message(question, stream=True)
    return response
# Global variable to store the current user's details
current_user_details = {}

@app.route("/chat", methods=["POST"])
def CustomChatGPT():
    global current_user_details

    # Retrieve user input from the request
    user_input = request.json.get("user_input", "")

    # If the user input is a name, update current_user_details
    if any(user_input.lower() == user['name'].lower() for user in resume_data):
        for user in resume_data:
            if user_input.lower() == user['name'].lower():
                current_user_details = user
                break
        response_message = f"Hi {current_user_details['name']}, how can I assist you today?"
    elif user_input.lower().startswith("change name to "):
        new_name = user_input.split("change name to ")[1]
        current_user_details = next((user for user in resume_data if user["name"].lower() == new_name.lower()), {})
        if current_user_details:
            response_message = f"Changed name to {current_user_details['name']}."
        else:
            response_message = f"Sorry, I couldn't find a user with the name '{new_name}'."
    else:
        # Check if the current_user_details is set
        if current_user_details:
            # Check if the user's input is a personal question
            if "name" in user_input.lower():
                response_message = f"The name of the person is {current_user_details['name']}."
            elif "skills" in user_input.lower():
                response_message = f"The skills of the person include {current_user_details['skills']}."
            elif "education" in user_input.lower():
                response_message = f"The education of the person is from {current_user_details['education']}."
            elif "experience" in user_input.lower():
                response_message = f"The person's experience is {current_user_details['experience']}."
            elif "certification" in user_input.lower():
                response_message = f"The person is certified by {current_user_details['certifications']}."
            elif "projects" in user_input.lower():
                response_message = f"The person has done {current_user_details['projects']} projects."
            elif "languages" in user_input.lower():
                response_message = f"The person knows languages such as {current_user_details['languages']}."
            # Add more conditions for other personal questions as needed
            else:
                
                response = get_gemini_response(user_input)
                response_message=""
                for r in response:
                    response_message+=r.text
                
        else:
            response_message = "Please provide the name of the person first."

    # Return the response
    return jsonify({"response": response_message})






# callback 
@app.route('/callback', methods=['POST'])
def CallBack():
    data = request.json  # Assuming the frontend sends data in JSON format
    db.callback.insert_one(data)
    print(data)

    return jsonify({"message": "Feedback submitted successfully!"})

# scan resume 

@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    try:
        # Assuming the file is sent as 'resume' in the form data
        uploaded_file = request.files['resume']

        if uploaded_file:
            # Save the file to a location (optional)
            uploaded_file.save('uploads/' + (uploaded_file.filename))

            # Extract information from the resume
            resume_data = resume_parser(uploaded_file.read())
            return jsonify(resume_data)

        return jsonify({'error': 'No file provided'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500




# @app.route('/submit_resume', methods=['POST'])
# def submit_resume():
#     try:
#         data = request.json  # Assuming data is sent as JSON

#         # Append the new data to the existing list
#         resume_data.append(data)

#         # Save the updated data back to the JSON file
#         with open(JSON_FILE_PATH, 'w') as file:
#             json.dump(resume_data, file, indent=4)

#         return jsonify({'message': 'Resume submitted successfully'}), 200
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500



@app.route('/submit_resume', methods=['POST'])
def submit_resume():
    try:
        user_input = request.data
        user_input=literal_eval(user_input.decode('utf-8'))
        try:
           db.resume.insert_one({"name":user_input["name"],"email":user_input["email"], "phone":user_input["phone"], 
                               "education":user_input["education"], "skills":user_input["skills"], "experience":user_input["experience"],
                               "certifications":user_input["certifications"],"projects":user_input["projects"],"languages":user_input["languages"]})
        except Exception as e:
            return "Error in db"
        return jsonify({'message': 'Resume submitted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/login", methods=["GET", "POST"])
def Login():
    if request.method == 'POST':
        user_input = request.data
        user_input=literal_eval(user_input.decode('utf-8'))
       
        
        existing_user = db.user.find_one({'email': user_input["user"]["email"]})
        
        if not existing_user:
            return jsonify({'message': 'No Email exists'}), 400
        
        
        user_db=db.user.find_one({"email":user_input["user"]["email"]})
        
        if user_db['password']==user_input["user"]["password"]:
            # current_user_details['email'] = existing_user['email']
            # current_user_details['name'] = existing_user['name']
            return jsonify({'message': 'Login successful'}), 200
        else:
            return jsonify({'message': 'Invalid email or password'}),401
    
# signup

@app.route("/signup", methods=["GET", "POST"])
def Signup():
    if request.method == 'POST':
        user_input = request.data
        user_input=literal_eval(user_input.decode('utf-8'))
        # print(user_input["user"]["email"])
        # print(type(json.loads(user_input["user"])))
        user_input=json.loads(user_input["user"])
        print(user_input)
        # Check if the email is already registered
        #  print(collection.find_one({"_id": ObjectId("59d7ef576cab3d6118805a20")}))
        
        existing_user = db.user.find_one({'email': user_input["email"]})
        
        if existing_user:
            return jsonify({'message': 'Email already exists'}), 400
        try:
           db.user.insert_one({"name":user_input["name"],"email":user_input["email"], "password":user_input["password"]})
        except Exception as e:
            return "Error in db"
        return jsonify({'message': 'Registration successful'}), 200
if __name__ == '__main__':
    app.run(debug=False)
