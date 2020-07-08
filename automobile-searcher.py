import argparse
import socket

import requests
import urllib3
from bs4 import BeautifulSoup
import json
import os.path
import telegram_send
import time as t

parser = argparse.ArgumentParser()
parser.add_argument("--name", "--add", dest='name', help="name of new tracking to be added")
parser.add_argument("--url", help="url for your new tracking's search query")
parser.add_argument("--delete", help="name of the search you want to delete")
parser.add_argument('--refresh', '-r', dest='refresh', action='store_true', help="refresh search results")
parser.set_defaults(refresh=False)
parser.add_argument('--list', '-l', dest='list', action='store_true', help="print a list of current trackings")
parser.set_defaults(list=False)
parser.add_argument('--short_list', dest='short_list', action='store_true', help="print a more compact list")
parser.set_defaults(short_list=False)
parser.add_argument('--loop', dest='loop', help='time of looping')

args = parser.parse_args()
queries = dict()
dbFile = r"D:\\Marco\\Universita\\Progetti\\automobile-it-searcher\\searches.tracked"
DEBUG = True
FILE_OUTPUT = r"D:\\Marco\\Universita\\Progetti\\automobile-it-searcher\\stdout.txt"

#def stampa(testo, debug_mode=False):
    #if debug_mode == True:
        #print(testo, file=FILE_OUTPUT)

def loop(time):
    while True:
        refresh()
        t.sleep(int(time))


# load from file
def load_from_file(fileName):
    global queries
    if not os.path.isfile(fileName):
        return

    with open(fileName) as file:
        queries = json.load(file)


def print_queries():
    global queries
    #print(queries, "\n\n")
    for search in queries.items():
        print("\nsearch: ", search[0])
        for query_url in search[1]:
            print("query url:", query_url)
            for url in search[1].items():
                for result in url[1].items():
                    print("\n", result[1].get('title'), ":", result[1].get('price'), "-->", result[1].get('location'))
                    print(" ", result[0])


# printing a compact list of trackings
def print_sitrep():
    global queries
    i = 1
    for search in queries.items():
        print('\n{}) search: {}'.format(i, search[0]))
        for query_url in search[1]:
            print("query url:", query_url)
        i = i+1


def refresh():
    global queries
    for search in queries.items():
        for query_url in search[1]:
            run_query(query_url, search[0])


def delete(toDelete):
    global queries
    queries.pop(toDelete)


def run_query(url, name):
    print("running query (\"{}\" - {})...".format(name, url))
    global queries
    try:
        page = requests.get(url)
        soup = BeautifulSoup(page.text, 'html.parser')
        product_list_items = soup \
            .find('div', class_='jsx-3810883459 Container') \
            .find('div', class_='jsx-3810883459 Container__Right') \
            .find('div', class_='jsx-1584082732 jsx-673266420 Contents') \
            .find_all('div', class_='jsx-3462268742 Card')
        # print(product_list_items[0])
        msg = []

        for product in product_list_items:
            card_box = product.find('div', class_='jsx-3462268742 Card__BoxTitleDesc')
            title = card_box.find('header', class_='jsx-3462268742').find('h2').contents[0]

            price_box = card_box.find('span', class_='jsx-3462268742 Card__InfoPriceMobile font-medium')
            # print(price_box)
            if (price_box is not None):
                # tmp = product.find('div', class_='AdElements__ItemPrice--container-L2hvbWUv').find('h6').contents
                price = price_box.decode_contents()

            else:
                price = "Unknown price"
            link = "https://www.automobile.it" + product.get('data-link')

            location = product.find('div', class_='jsx-3462268742 Card__InfoLocation font-base').find('span').contents[
                0]

            if not queries.get(name):  # insert the new search
                queries[name] = {url: {link: {'title': title, 'price': price, 'location': location}}}
                print("\nNew search added:", name)
                print("Adding result:", title, "-", price, "-", location)
            else:  # add search results to dictionary
                if not queries.get(name).get(url).get(link):  # found a new element
                    tmp = "New element found for " + name + ": " + title + " @ " + price + " - " + location + " --> " + link + '\n'
                    msg.append(tmp)
                    queries[name][url][link] = {'title': title, 'price': price, 'location': location}

        if len(msg) > 0:
            telegram_send.send(messages=msg)
            print("\n".join(msg))
            print('\n{} new elements have been found.'.format(len(msg)))
            save(dbFile)
        else:
            print('\nAll lists are already up to date.')
        # print("queries file saved: ", queries)
    except (socket.gaierror, urllib3.exceptions.NewConnectionError, urllib3.exceptions.MaxRetryError, requests.exceptions.ConnectionError):
        print("Errore di connessione")

def save(fileName):
    with open(fileName, 'w') as file:
        file.write(json.dumps(queries))

# def get_auto_acc(url: str):
#     global queries
#     try:
#         for
#         page = requests.get(url)
#         soup = BeautifulSoup(page.text,'html.parser')



if __name__ == '__main__':

    load_from_file(dbFile)
    
    if args.list:
        print("printing current status...")
        print_queries()
    
    if args.short_list:
        print('printing quick sitrep...')
        print_sitrep()

    if args.url is not None and args.name is not None:
        run_query(args.url, args.name)

    if args.refresh:
        refresh()

    if args.delete is not None:
        delete(args.delete)

    if args.loop is not None:
        loop(args.loop)
    print()
    save(dbFile)
