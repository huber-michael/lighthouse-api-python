import requests
import json
import os
from binascii import a2b_base64
from pathlib import Path
from urllib.parse import urlparse
from urllib import request
import pandas as pd
import traceback

printoutput = False
#####
index = 1
# auditlist = ('speed-index','first-contentful-paint','total-byte-weight','first-meaningful-paint','time-to-first-byte','first-contentful-paint-3g','interactive','structured-data')

##### SETTINGS ######

# What Categories to check
categorieslist = ('seo','performance','best-practices')#'accessibility','pwa')
# For which audits to export detailed info
detailsexport = ('resource-summary','network-requests','total-byte-weight','unused-css-rules','errors-in-console','bootup-time','mainthread-work-breakdown','dom-size','unminified-javascript','uses-long-cache-ttl','tap-targets','deprecations','render-blocking-resources','third-party-summary')
# Strategy (mobile or desktop), since google switched to mobile first set to mobile
strategy = 'mobile'
# If you do regular request and automate it, go get an API-Key and put it there
apikey = '' # '&key=YOURKEY'


##### END ######
lhcategories = ''

for category in categorieslist:
    lhcategories = lhcategories + "&category="+category

with open('urllist.json') as json_file:
    data = json.load(json_file)
    for url in data['urls']:
        print("\nStart Lighthouse-Test for " + url)

        lhscores = []
        catscores = []
        # build the path where results will be saved. uses url as base
        urlelements = urlparse(url)
        domainp = urlelements.netloc.replace('.', '-')
        path = urlelements.path
        if not path.endswith('/'):
            path = path + '/'
        basepath = os.getcwd() + "/testresults/" + domainp + path
        filename = basepath + 'result.json'
        result = Path(basepath + 'result.json')
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        #check if there is already a resultset for the url
        if not result.is_file():
            x = f'https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={url}{lhcategories}&strategy={strategy}{apikey}&locale=de-DE'
            response = requests.get(x)
            lhtest = response.json()
            if lhtest.get('id',False):
                with open(basepath + 'result.json', 'w+') as re:
                    jsonstr = json.dumps(lhtest, ensure_ascii=False, indent=4)
                    re.write(jsonstr)
                    re.close()
        else:
            with open(result, 'r+') as tmp:
                lhtest = json.load(tmp)
                tmp.close()
        try:
            print("\nResults fetched from api")
        except KeyError:
            print("Request was not successful")
            print(lhtest)
            exit()
        try:
            url = lhtest['id']

            # dl image
            screen = lhtest['lighthouseResult']['audits']['final-screenshot']['details']['data']
            response = request.urlopen(screen)
            with open(basepath + 'rendered.jpg', 'wb') as f:
                f.write(response.file.read())
                f.close()
                
            thumbs = lhtest['lighthouseResult']['audits']['screenshot-thumbnails']['details']['items']
            for thumb in thumbs:
                with open(basepath + 'thumbnail' + str(thumb['timing']) + '.jpg', 'wb') as f:
                    response = request.urlopen(thumb['data'])
                    f.write(response.file.read())
                    f.close()

            if printoutput: print("\n\nResources\n")
            resources = lhtest['lighthouseResult']['audits']['resource-summary']['details']['items']
            if printoutput: print("{:<40}|{:>20}|{:>20} ".format('Resource-Type', 'Size', 'Number of Items'))
            if printoutput: print("{:=<40}|{:=>20}|{:=>20} ".format('', '', ''))
            for resource in resources:
                if printoutput: print("{:<40}|{:>20}|{:>20}".format(resource.get('label',''), resource.get('size',0), resource.get('requestCount',0)))
                if printoutput: print("{:-<40}|{:->20}|{:->20} ".format('', '', ''))
            auditref_lis = {}
            for categories in lhtest['lighthouseResult']['categories']:
                catscore  = lhtest['lighthouseResult']['categories'][categories]['score']
                catid = lhtest['lighthouseResult']['categories'][categories]['id']
                cattitle = lhtest['lighthouseResult']['categories'][categories]['title']
                catvalue = lhtest['lighthouseResult']['categories'][categories].get('description','')
                catscores.append({"id": catid, "title": cattitle, "score": catscore, "value": catvalue})
                for auditref in lhtest['lighthouseResult']['categories'][categories]['auditRefs']:
                    if printoutput: print (categories,"-->", auditref['id'])
                    auditref_lis[auditref['id']] = {"maincat": categories, "subcat": auditref.get('group',''), "weight": auditref.get('weight',0)}

            if printoutput: print("\n\nCategories-Results\n")
            if printoutput: print("{:<40}|{:>40} ".format('Test', 'Score'))
            if printoutput: print("{:=<40}|{:=>40}".format('', '', ''))
            for singlescore in catscores:
                    if printoutput: print("{:<40}|{:>40}".format(singlescore.get('title', ''), singlescore.get('score', 0)))
                    if printoutput: print("{:-<40}|{:->40} ".format('', '', ''))

    ### Auditspart
            for audit in lhtest['lighthouseResult']['audits']:
                id = lhtest['lighthouseResult']['audits'][audit].get('id',False)
                title = lhtest['lighthouseResult']['audits'][audit].get('title',False)
                score = lhtest['lighthouseResult']['audits'][audit].get('score','NA')
                desc = lhtest['lighthouseResult']['audits'][audit].get('description',False)

                if score and score >= 1:
                    dv = 'OK'
                    dv = lhtest['lighthouseResult']['audits'][audit].get('displayValue', False)

                else:
                    dv = lhtest['lighthouseResult']['audits'][audit].get('displayValue', False)
                if score:
                    lhscores.append({'id': id, 'lable': title, 'group': str(auditref_lis[id]['maincat']),'subgroup': str(auditref_lis[id]['subcat']),'weight': str(auditref_lis[id]['weight']), 'score': score, 'value': dv, 'desc': desc})

            if printoutput: print("\n\nAudit-Results\n")
            if printoutput: print("{:<40}|{:>20}|{:>20}|{:>40} ".format('Test', 'Group', 'Score', 'Info'))
            if printoutput: print("{:=<40}|{:=>20}|{:=>20}|{:=>40} ".format('', '', '',''))

            lhscores = sorted(lhscores, key=lambda i: i['group'])

            for singlescore in lhscores:
                if singlescore.get('group') in categorieslist:
                    lable = singlescore.get('lable','') if len(singlescore.get('lable','')) < 37 else singlescore.get('lable','')[0:37] + "..."
                    if printoutput: print("{:<40}|{:>20}|{:>20}|{:>40}".format(lable,
                                                               singlescore.get('group',''),
                                                               singlescore.get('score',0),
                                                               singlescore.get('value',0)))
                    if printoutput: print("{:-<40}|{:->20}|{:->20}|{:->40} ".format('', '', '',''))
            writer = pd.ExcelWriter(basepath + 'results.xlsx')
            # save categorie results
            json_data = json.dumps(catscores)
            data = pd.read_json(json_data)
            data.to_excel(writer, 'categories', index=False)
            writer.save()
            # save overview of audit results
            json_data = json.dumps(lhscores)
            data = pd.read_json(json_data)
            data.to_excel(writer, 'audits', index=False)
            writer.save()
            # save details of audits for defined set
            for audit in detailsexport:
                id = lhtest['lighthouseResult']['audits'][audit].get('id', False)
                hasdetails = lhtest['lighthouseResult']['audits'][audit].get('details',False)
                if id and hasdetails and len(lhtest['lighthouseResult']['audits'][audit]['details'].get('items',[])) > 0:
                    json_data = json.dumps(lhtest['lighthouseResult']['audits'][audit]['details']['items'])
                    data = pd.read_json(json_data)
                    data.to_excel(writer, audit, index=False)
                    writer.save()
        except KeyError as e:
            print(f'<KeyError> One or more keys not found {e}.')
            print(traceback.format_exc())
        print("Testresults saved to: " + basepath + 'results.xlsx')
        print("Lighthouse-Test finished without Errors for " + lhtest['id'] + '\n')
