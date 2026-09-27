from app.services.timeline import get_patient_timeline


timeline = get_patient_timeline(4)

for item in timeline:
    print(item)