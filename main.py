import os
import json

source_dir = "data"
output_file = 'output.json'
all_files = os.listdir(source_dir)

def getJsonType(d):
    if "scores" in d or "lastScores" in d:
        return "scores"
    if "[user](#message)" in d.values():
        return "user"
    if "[assistant](#message)" in d.values():
        return "assistant"

def splitListByScore(source_data):
    result = []
    tmp = []
    for item in source_data:
        if getJsonType(item) != "scores":
            tmp.append(item)
        elif tmp:
            tmp.append(item)
            result.append(tmp)
            tmp = []
    if tmp:
        result.append(tmp)
    return result

def isUserModified(d):
    return d["text"] == "@"

def calculate_score(s):
    digits = s.split('@')[1]
    score = sum(int(d) for d in digits)
    return score+(int(digits)/10000)

def getBestBot(d):
    scored_elements = []
    score_list = d["scores"] if "scores" in d else d["lastScores"]
    if score_list == []:
        return None
    for elem in score_list:
        score = calculate_score(elem)
        scored_elements.append((score, elem))
    scored_elements.sort(reverse=True) 
    sorted_elements = [elem for _, elem in scored_elements]
    return sorted_elements[0].split("@")[0]

def getQaList(source_data):
    result = []
    tmp = []
    lock = False
    for item in source_data:
        if getJsonType(item) == "user":
            if not lock:
                tmp.append(item)
                lock = True
            else:
                if len(tmp) > 1:
                    result.append(tmp)
                tmp = [item]
        else:
            tmp.append(item)
    if tmp and len(tmp) > 1:
        result.append(tmp)
    return result

def getQaMsg(msg_list):
    result = []
    best_bot = getBestBot(msg_list[-1])
    msg_list = msg_list[:-1]
    qa_list = getQaList(msg_list)
    for qa in qa_list:
        tempDict = {"question":qa[0]["text"],"generated":"###","type":0}
        if best_bot:
            order_dict = {"modified":3, "best_bot":2, "other":1}
        else:
            order_dict = {"modified":3, "other":1}
        for msg in qa[1:]:
            if msg["text"][0] != "@":
                tempDict["generated"] = msg["text"]
                tempDict["type"] = order_dict["modified"]
                break
            elif best_bot is not None and best_bot in msg["text"]:
                if tempDict["type"] < order_dict["best_bot"]:
                    tempDict["generated"] = msg["text"]
                    tempDict["type"] = order_dict["best_bot"]
            else:
                if not tempDict["type"]:
                    tempDict["generated"] = msg["text"]
                    tempDict["type"] = order_dict["other"]
        answer = tempDict["generated"].split(" ", 1)[1].strip()  if "@" == tempDict["generated"][0] else tempDict["generated"]
        result.append({"question":tempDict["question"],"generated":answer})
    return result

source_data = []   
for file in all_files:
    source_file = os.path.join(source_dir, file)
    with open(source_file, "r", encoding="utf-8") as f:
        temp_data_list = json.load(f)
        temp_data_list = temp_data_list[1:]
        source_data.extend(temp_data_list)
splited_source_data = splitListByScore(source_data)
qa_list = []
for item in splited_source_data:
    qa_list.extend(getQaMsg(item))

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(qa_list, f, ensure_ascii=False, indent=4)