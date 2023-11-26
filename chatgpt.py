from fastapi import FastAPI, HTTPException
from openai import OpenAI
from kineticforms import KineticForms
from kineticemail import KineticEmail

class MyOpenAI:

    def __init__(self, db_connection):
        self.kf = KineticForms(db_connection)

    def chat(self, email, prompt: str, message_id):
        a = open("/Users/user/openapi_key.txt", "r").read().strip('\n')
        client = OpenAI(
            # defaults to os.environ.get("OPENAI_API_KEY")
            api_key=a
        )
        history = self.kf.sql("select * from pdf_chat where from_address = '" + email + "' order by id")

        messages = []
        # for m in history['data']:
        #    message = {"role": m['role'], "content": m['contents']}
        #    messages.append(message)

        messages.append({"role": "user", "content": prompt})

        try:
            self.save_chat(email, "user", prompt)
            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=3000
            )
            somthing = completion.choices[0].message.content
            print(somthing)
            self.save_chat(email, completion.choices[0].message.role, somthing)
            ke = KineticEmail('/var/gptpwd.json')
            # m = ke.get_message_by_id(message_id, "Inbox")
            ke.reply_to_email(message_id, somthing, '/Users/user/Downloads/a.pdf')
            #return completion
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"1 Error processing POST data: {str(e)}")

    def clear_chat(self):
        sql = "delete from pdf_chat"
        self.kf.execute(sql)
        return {"result": "done"}

    def save_chat(self, email: str, role: str, content: str):
        post = {"table_name": "pdf_chat", "action": "insert", "role": role, "contents": content, "from_address": email}
        print(post)
        self.kf.post(post)
