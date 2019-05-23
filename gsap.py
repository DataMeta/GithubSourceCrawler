# Daniel Melnikov
# Github Source Code Analysis 
# Version 1.1

from github import Github
from wordgen import *
import base64
import re
import time
import random
import logging
import winsound
import enchant
import datetime

freq = 650 # in Hz
dur = 300 # in ms

class GitHubSourceCrawler():
    
    # Initializes instance of GitHub object for use with the API
    # Initializes  
    def __init__(self, string):
        self.github = Github(string)
        dict_lookup = enchant.Dict("en_US")

    # Actually gave me an idea for combatting an anti-ddos response
    def start_dialog(self):
        rand = 1 + random.random()
        print("Accessing Github API ...")
        time.sleep(rand * random.random())
        print("Please wait ...")
        time.sleep(rand * random.random())
        print()

    # Handles input for user search
    def search_dialog(self, query, query_addon):
        # print("Launch search query when ready:")
        # input("> ")
        query = query + " " + query_addon
        user_list = self.github.search_users(query, "repositories", "asc")
        return (user_list, query)

    # Fast duplicate removal which preserves order for debugging
    def uniquify(self, seq):
        seen = set()
        seen_add = seen.add
        return [x for x in seq if not (x in seen or seen_add(x))]

    # Acquires the secure hash for a repository commit, where tag is always 'master'.
    def get_sha_for_tag(self, repository, tag):
        branches = repository.get_branches()
        matched_branches = [match for match in branches if match.name == tag]
        if matched_branches:
            return matched_branches[0].commit.sha
     
        tags = repository.get_tags()
        matched_tags = [match for match in tags if match.name == tag]
        if not matched_tags:
            raise ValueError('No Tag or Branch exists with that name')
        return matched_tags[0].commit.sha

    # Downloads all contents at path with commit tag "sha" in the repository.
    def download_directory(self, repository, sha, server_path, source_container):
        try:
            contents = repository.get_dir_contents(server_path, ref=sha)
            for content in contents:
                print ("Processing %s" % content.path)
                if content.type == 'dir':
                    self.download_directory(repository, sha, content.path, source_container)
                else:
                    if content.size < 1000000: # Github API limits file size
                        try:
                            if content.path.endswith(".java"):
                                path = content.path
                                file_content = repository.get_contents(path, ref=sha)
                                file_data = base64.standard_b64decode(file_content.content)
                                data_string = file_data.decode(encoding='UTF-8')
                                source_container.append(data_string)
                        except (Exception, IOError) as exc:
                            logging.error('Error processing %s: %s', content.path, exc)
        except (Exception) as exc:
            logging.error('An exception occured while downloading directory: ', exc)
        return source_container

    # Parses for all variables in a repository
    def parse_variables(self, repository, sha, server_path):
        source_container = []
        dir_content = self.download_directory(repository, sha, server_path, source_container)
        re_pattern = r'(?:(?:static\s*|final\s*|volatile\s*|byte\s*|Byte\s*|short\s*|Short\s*|long\s*|Long\s*|int\s*|Integer\s*|float\s*|Float\s*|String\s*)+)(?:\s+\*?\*?\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*[\[;,=)]'
        length = 0
        count = 0
        dictword_count = 0
        for content in dir_content:
            matches = re.findall( re_pattern, content, re.DOTALL)
            for match in matches:
                if not None:
                    print(match) # Debugging visual aid
                    if dict_lookup.check(match):
                        dictword_count += 1
                    length += len(match)
                    count += 1
        print()
        package = (length, count, dictword_count)
        return package

    # Get owner commit ratio for a repo (to determine primary or majority contributor)
    def check_commits(self, repository, sha, server_path):
        print("\nCHECKING REPOSITORY COMMITS")
        owner_commits = 0
        total_commits = 0
        commits = repository.get_commits(sha, server_path)
        for commit in commits:
            # Request rate governor; 
            # Keeps program from triggering denial of service false positive
            # if total_commits%1000 == 0:
            #     time.sleep(.999)
            # if total_commits%100 == 0:
            #     time.sleep(.099)
            # if total_commits%10 == 0:
            #     time.sleep(.009)
            print(".", end=" ") # To see the program working during debug
            total_commits += 1
            if commit.author == repository.owner:
                owner_commits += 1
        print()
        return owner_commits/total_commits

    # Crawls user's repos and analyzes source code that is from repos 
    #   for which the user is a majority contributor 
    # Determines average variable length and ratio of variables found in the dictionary
    def analyze_user(self, user):
        rand = 1 + random.random()
        #time.sleep(rand * random.random())
        path = ''
        total_length = 0
        total_count = 0
        total_dictwords = 0
        commit_ratio = -1
        repositories = user.get_repos()
        for repository in repositories:
            time.sleep(rand * random.random()) # Keeps the connection from being closed from suspicion of dos attack
            try:
                sha = self.get_sha_for_tag(repository, 'master')
                try:
                    commit_ratio = self.check_commits(repository, sha, path)
                except (Exception) as exc:
                    logging.error('Commit(s) not found: ', exc)
                if  commit_ratio >= .5:
                    package = self.parse_variables(repository, sha, path)
                    total_length += package[0]
                    total_count += package[1]
                    total_dictwords += package[2]
            except (Exception) as exc:
                logging.error('No master branch exists for this repo: ', exc)
            #time.sleep(rand * random.random())
        data = (total_length, total_count, total_dictwords)
        return data

    # Handles processing of user sample 
    def process_user_sample(self, user_list):
        print("\n[][][]PROCESSING USER SAMPLE[][][]")
        result_length = 0
        result_count = 0
        result_dictwords = 0
        user_count = 0
        for user in user_list:
            user_count += 1
            print("\n-----\nANALYZING USER #", user_count)
            print("-----")
            data = self.analyze_user(user)

            # Saves each user's data without query and run time in case the 
            # github API rate limit is hit and program interrupts
            self.log_data(-1,user_count,data,-1) 
            result_length += data[0]
            result_count += data[1]
            result_dictwords += data[2]
        result = (result_length, result_count, result_dictwords)
        return result

    # Wrapper method that handles the search and analysis run
    def launch_handler(self):
        query_addon = "in:login type:user language:java followers:3"
        query = Random_Word(3) # Generates a word of input length
        print ("Query: ", query, query_addon)
        search_query = query + " " + query_addon
        #search_query = query_addon/
        user_list = self.github.search_users(search_query, "followers", "asc")

        print("\nUser(s) found:")
        user_count = 0
        try:
            for user in user_list:
                user_count += 1
                print("#", user_count, user.login)
        except (Exception) as exc:
            logging.error('Search API rate limit exceeded')
            
        payload = []
        for i in range(user_count):
            payload.append(user_list[i])

        print("\nMANUAL LAUNCH: ")
        input("> ")
        start_time = time.clock()
        result = self.process_user_sample(payload)
        stop_time = time.clock()
        elapsed = stop_time - start_time
        self.log_data(search_query, user_count, result, elapsed)

    # Writes data to file
    def log_data(self, search_query, user_count, result, elapsed):
        result_length = result[0]
        result_count = result[1]
        result_dictwords = result[2]
        results_file = open('results3.txt', 'a')

        results_file.write("{}\n".format(search_query))
        results_file.write("{}\n".format(user_count))
        results_file.write("{}\n".format(result_length))
        results_file.write("{}\n".format(result_count))
        results_file.write("{}\n".format(result_dictwords))
        results_file.write("{}\n\n".format(elapsed))
        results_file.close()

    def check_rate_limit(self): 
        print("Requests remaining: ", self.github.rate_limiting[0])
        print("Request max: ", self.github.rate_limiting[1])
        value = datetime.datetime.fromtimestamp(self.github.rate_limiting_resettime)
        print("Rate limit reset time, ", value.strftime('%Y-%m-%d %H:%M:%S'))


# Start of main program

# Initialize Github object with token string associated with your GitHub username
gsap = GitHubSourceCrawler("AUTHENTICATION TOKEN STRING GOES HERE")
gsap.start_dialog()
gsap.launch_handler()
gsap.check_rate_limit()

#winsound.Beep(freq,dur)
#input("\nPress \"Enter\" to exit: \n"
