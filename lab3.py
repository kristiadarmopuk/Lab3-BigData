import json
from pymongo import MongoClient


def connect_to_mongo():
  client = MongoClient("mongodb://localhost:27017/")
  db = client["hospital_db"]
  collection = db["hospitals"]
  return collection


def load_initial_data(collection):
  if collection.count_documents({}) == 0:
    try:
      with open("hospitals_mongodb.json", "r", encoding="utf-8") as file:
        data = json.load(file)
        if data:
          collection.insert_many(data)
          print(f"[Успіх] Завантажено {len(data)} записів у базу даних.")
    except FileNotFoundError:
      print(
          "[Попередження] Файл 'hospitals_mongodb.json' не знайдено."
          " Переконайтеся, що файл у тій самій папці."
      )
  else:
    print("[Інфо] База даних уже містить записи.")

def format_number(value):
  if value is None:
    return "0.00"
  return f"{value:,.2f}".replace(",", " ")

def step_1_count_documents(collection):
  count = collection.count_documents({})
  print(f"\n--- КРОК 1: Кількість документів у колекції ---")
  print(f"Загальна кількість документів: {count}")


def step_2_sum_covered_charges(collection):
  pipeline = [{
      "$group": {"_id": None, "total_charges": {"$sum": "$Average_Covered_Charges"}}
  }]
  result = list(collection.aggregate(pipeline))

  print(f"\n--- КРОК 2: Загальна сума Average_Covered_Charges ---")
  if result:
    formatted_sum = format_number(result[0]["total_charges"])
    print(f"Сума: {formatted_sum}")
  else:
    print("Дані відсутні.")


def step_3_sum_by_state(collection):
  pipeline = [
      {
          "$group": {
              "_id": "$Provider_State",
              "total_charges": {"$sum": "$Average_Covered_Charges"},
          }
      },
      {
          "$sort": {"total_charges": -1}
      },
  ]
  results = list(collection.aggregate(pipeline))

  print(
      f"\n--- КРОК 3: Сума Average_Covered_Charges по штатах (упорядковано) ---"
  )
  for r in results:
    formatted_sum = format_number(r["total_charges"])
    print(f"Штат: {r['_id']} | Сума: {formatted_sum}")


def step_4_sum_by_state_filtered(collection):
  try:
    threshold = float(
        input("Введіть порогове значення для суми (наприклад, 1000000): ")
    )
  except ValueError:
    threshold = 1000000.0
    print(f"Використано значення за замовчуванням: {threshold}")

  pipeline = [
      {
          "$group": {
              "_id": "$Provider_State",
              "total_charges": {"$sum": "$Average_Covered_Charges"},
          }
      },
      {
          "$match": {"total_charges": {"$gt": threshold}}
      },
      {"$sort": {"total_charges": -1}},
  ]
  results = list(collection.aggregate(pipeline))

  formatted_threshold = format_number(threshold)
  print(f"\n--- КРОК 4: Штати з сумою > {formatted_threshold} ---")
  if results:
    for r in results:
      formatted_sum = format_number(r["total_charges"])
      print(f"Штат: {r['_id']} | Сума: {formatted_sum}")
  else:
    print("Немає штатів, що задовольняють умову.")


def step_5_filtered_discharges_and_charges(collection):
  try:
    threshold = float(
        input(
            "Введіть порогове значення суми для Кроку 5 (наприклад, 500000): "
        )
    )
  except ValueError:
    threshold = 500000.0
    print(f"Використано значення за замовчуванням: {threshold}")

  pipeline = [
      {
          "$match": {"Total_Discharges": {"$gt": 20}}
      },
      {
          "$group": {
              "_id": "$Provider_State",
              "total_charges": {"$sum": "$Average_Covered_Charges"},
          }
      },
      {
          "$match": {"total_charges": {"$gt": threshold}}
      },
      {"$sort": {"total_charges": -1}},
  ]
  results = list(collection.aggregate(pipeline))

  formatted_threshold = format_number(threshold)
  print(
      f"\n--- КРОК 5: Сума по штатах (Total_Discharges > 20, сума >"
      f" {formatted_threshold}) ---"
  )
  if results:
    for r in results:
      formatted_sum = format_number(r["total_charges"])
      print(f"Штат: {r['_id']} | Сума: {formatted_sum}")
  else:
    print("Немає результатів за заданими умовами.")

def main():
  collection = connect_to_mongo()
  load_initial_data(collection)

  while True:
    print("\n                       МЕНЮ ")
    print("1. Крок 1: Кількість документів у колекції")
    print("2. Крок 2: Сума поля Average_Covered_Charges")
    print("3. Крок 3: Сума Average_Covered_Charges по штатах (з сортуванням)")
    print("4. Крок 4: Сума по штатах (фільтр за сумою + сортування)")
    print("5. Крок 5: Сума по штатах (Total_Discharges > 20 + фільтр + сортування)")
    print("6. Вихід")

    choice = input("Оберіть пункт завдання (1-6): ").strip()

    if choice == "1":
      step_1_count_documents(collection)
    elif choice == "2":
      step_2_sum_covered_charges(collection)
    elif choice == "3":
      step_3_sum_by_state(collection)
    elif choice == "4":
      step_4_sum_by_state_filtered(collection)
    elif choice == "5":
      step_5_filtered_discharges_and_charges(collection)
    elif choice == "6":
      print("Вихід з програми. До побачення!")
      break
    else:
      print("[Помилка] Невірний вибір. Введіть число від 1 до 6.")


if __name__ == "__main__":
  main()