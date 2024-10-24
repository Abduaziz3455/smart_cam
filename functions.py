import os.path
from datetime import datetime as dt
from uuid import uuid4
import cv2
import numpy as np
from smart_cam.database import Database

from smart_cam.deepface.extendedmodels import Age, Gender, Race, Emotion
from smart_cam.deepface.DeepFace import build_model

# models = {"age": build_model("Age"), "gender": build_model("Gender"), "emotion": build_model("Emotion")}
# "emotion": build_model("Emotion")
# "age": build_model("Age")
# "emotion": build_model("Emotion"),
# "gender": build_model("Gender"),
# "race": build_model("Race")

db = Database()


def main_function(face_loc, name, dis, encod, frame, red_db, enter: bool, distance_threshold=0.58):
    # Unpack face_loc coordinates
    y1, x2, y2, x1 = face_loc
    if name == 'Unknown' and dis > distance_threshold:
        client_name = f"new-{str(uuid4())}"
        image_path = f"media/clients/images/{client_name}.jpg"
        current_time = dt.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        # Create a new row for the DataFrame
        new_row = {
            'name': client_name, 'array_bytes': encod, 'is_client': 'True',
            'created_time': current_time, 'last_time': current_time,
            'last_enter_time': current_time if enter else '',
            'last_leave_time': current_time if not enter else '',
            'enter_count': 1 if enter else 0,
            'leave_count': 1 if not enter else 0,
            'stay_time': 0,
            'image': image_path,
            'last_image': '',
        }
        cv2.imwrite(image_path, frame[y1 - 13:y2 + 13, x1 - 13:x2 + 13], [int(cv2.IMWRITE_JPEG_QUALITY), 100])
        # Append the new row to the DataFrame
        red_db.add_person(person=f"client:{client_name}", **new_row)
        print("Successfully saved")
    elif name != 'Unknown' and dis <= 0.42:
        # Check if the name exists in the DataFrame
        cond = red_db.get_field(name=f"client:{name}", field='last_time')
        if cond:
            current_time = dt.now()
            try:
                last_time = dt.strptime(cond, '%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                last_time = dt.strptime(cond, '%Y-%m-%dT%H:%M:%S.%f')
            time1 = current_time.time()
            time2 = last_time.time()

            # Calculate the time difference in minutes
            time_diff_minutes = (time1.hour * 60 + time1.minute) - (time2.hour * 60 + time2.minute)
            # Check if the time difference is greater than 5 minutes
            if abs(time_diff_minutes) > 5:
                # Update DataFrame entries for an existing face
                image_path = f"media/clients/last_images/{name}.jpg"
                cv2.imwrite(image_path, frame[y1 - 30:y2 + 30, x1 - 30:x2 + 30], [int(cv2.IMWRITE_JPEG_QUALITY), 70])

                row = {
                    'last_time': f"{current_time}",
                    'last_image': image_path,
                }

                if enter:
                    row['last_enter_time'] = f"{current_time}"
                    row['enter_count'] = 1
                else:
                    row['last_leave_time'] = f"{current_time}"
                    row['leave_count'] = 1
                    row['stay_time'] = int(time_diff_minutes)
                # update person
                red_db.update_person(person=f"client:{name}", **row)
                print("Updated!!!")
        else:
            is_client = True
            image_path = f"media/clients/images/{name}.jpg"
            if not os.path.exists(image_path):
                image_path = f"media/employees/images/{name}.jpg"
                if not os.path.exists(image_path):
                    return False
                is_client = False
            current_time = f"{dt.now()}"

            # Create a new row for the DataFrame
            new_row = {
                'name': name, 'status': True,
                'array_bytes': encod, 'is_client': f'{is_client}',
                'created_time': current_time, 'last_time': current_time,
                'last_enter_time': current_time if enter else '',
                'last_leave_time': current_time if not enter else '',
                'enter_count': 1 if enter else 0,
                'leave_count': 1 if not enter else 0,
                'stay_time': 0,
                'image': image_path,
                'last_image': '',
            }
            # Append the new row to the DataFrame
            red_db.add_person(person=f"client:{name}", **new_row)
            if is_client:
                print(f"{name[:6]} - Client successfully saved!")
            else:
                print(f"{name[:6]} Employee saved!")
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 200), 2)
    cv2.putText(frame, f"{name}-{dis:.2f}", (x1, y1 - 13), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 0, 200), 2)

    # age, gender, emotion
    # obj = {}
    # img_224 = np.expand_dims(cv2.resize(frame[y1:y2, x1:x2], (224, 224)), axis=0)
    # # #
    # img_emotion = np.expand_dims(cv2.resize(cv2.cvtColor(frame[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY), (48, 48)), axis=0)
    # # # # emotion
    # emotion_predictions = models["emotion"].predict(img_emotion, verbose=0)[0, :]
    #
    # sum_of_predictions = emotion_predictions.sum()
    # obj["emotion"] = {}
    #
    # for i, emotion_label in enumerate(Emotion.labels):
    #     emotion_prediction = 100 * emotion_predictions[i] / sum_of_predictions
    #     obj["emotion"][emotion_label] = emotion_prediction
    #
    # obj["dominant_emotion"] = Emotion.labels[np.argmax(emotion_predictions)]
    #
    # # age
    # age_predictions = models["age"].predict(img_224, verbose=0)[0, :]
    # apparent_age = Age.findApparentAge(age_predictions)
    # # int cast is for exception - object of type 'float32' is not JSON serializable
    # obj["age"] = int(apparent_age)
    # # gender
    # gender_predictions = models["gender"].predict(img_224, verbose=0)[0, :]
    # obj["gender"] = {}
    # for i, gender_label in enumerate(Gender.labels):
    #     gender_prediction = 100 * gender_predictions[i]
    #     obj["gender"][gender_label] = gender_prediction
    # # #
    # obj["dominant_gender"] = Gender.labels[np.argmax(gender_predictions)]
    # cv2.putText(frame, f"{obj['age']}-{obj['dominant_gender']}", (x1+50, y1 - 50),
    #             cv2.FONT_HERSHEY_DUPLEX, 1.5, (0, 0, 200), 3)
