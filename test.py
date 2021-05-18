import json

req = ['{"data":{"sportName":null,"lessonNumber":null,"lessonName":null,"lessonStart":null,"lessonEnd":null,"facilityId":null,"location":{"De":""},"room":{"De":null},"id":2172373,"lessonId":204074,"personId":139347,"status":4,"statusInfo":"4 - definitiv","webRegistrationTypeId":4,"webRegistrationType":"Einschreibung","invoiceId":0,"invoiceAmount":null,"paidAmount":0.0,"expiresOn":null,"paymentId":"","placeNumber":10,"changeDate":"2021-05-18T11:22:00.51+02:00","sourceIsIm":true}}']

l = json.loads(req[-1])
place = l["data"]["placeNumber"]
print(place)