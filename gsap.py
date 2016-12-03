# Daniel Melnikov
# Github Source Code Analysis (operative name)
# Version 1.7.4

from github import Github
import base64
import re
import time
import random
import logging
import winsound

freq = 650 # in Hz
dur = 300 # in ms

# Makes the program feel prettyful, does nothing. 
def init_it():
    rand = 1 + random.random()
    print("Accessing Github API ...")
    time.sleep(rand * random.random())
    print("Please wait ...")
    time.sleep(rand * random.random())
    print()

def search_dialog():
    print("Username to search for (part of username allowed):")
    user_query = input("> ")
    user_query += query_addon
    user_list = github.search_users(user_query, "repositories", "desc")
    return user_list

# Fast duplicate removal which preserves order for debugging
def uniquify(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]

# Acquires the secure hash for a repository commit, where tag is always 'master'.
def get_sha_for_tag(repository, tag):
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
def download_directory(repository, sha, server_path, source_container):
    contents = repository.get_dir_contents(server_path, ref=sha)
    
    for content in contents:
        print ("Processing %s" % content.path)
        if content.type == 'dir':
            download_directory(repository, sha, content.path, source_container)
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
    return source_container

# Parses for all variables in a repository
def parse_variables(repository, sha, server_path):
    source_container = []
    dir_content = download_directory(repository, sha, server_path, source_container)
    #re_pattern = r'(?:byte|Byte|short|Short|long|Long|int|Integer|float|Float|String)(\s[^\s]+)(?:\s=|;)'
    #re_pattern = r'((?:(?:static\s*|final\s*|volatile\s*|byte\s*|Byte\s*|short\s*|Short\s*|long\s*|Long\s*|int\s*|Integer\s*|float\s*|Float\s*|String\s*)+)(?:\s+\*?\*?\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*[\[;,=)])'
    re_pattern = r'(?:(?:static\s*|final\s*|volatile\s*|byte\s*|Byte\s*|short\s*|Short\s*|long\s*|Long\s*|int\s*|Integer\s*|float\s*|Float\s*|String\s*)+)(?:\s+\*?\*?\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*[\[;,=)]'
    
    length = 0
    count = 0

    for content in dir_content:
        matches = re.findall( re_pattern, content, re.DOTALL)
        for match in matches:
            if not None:
                print(match)
                length += len(match)
                count += 1
        
    if count > 0:
        average_length = length/count
        print("\nNumber of variables found in this repository: ", count)
        print("Average variable length in characters: ", average_length)
    else:
        print("No variables found")
    package = (length, count)
    return package


#Start of program
#input()
init_it()
# Initialize Github object with token associated with my username
github = Github("oauth") 
query_addon = " in:login type:user"# language:java" #Filter for users with java repos in the majority
user_list = search_dialog()

print("User(s) found:")
user_count = 0
try:
    for user in user_list:
        user_count += 1
        print("#", user_count, user.login)
except (Exception) as exc:
    logging.error('API rate limit exceeded')
    
print("\nSelection:")
user_num = int(input("> "))

user = user_list[user_num-1]
path = ''
repositories = user.get_repos()
total_length = 0
total_count = 0

start_time = time.clock()
# Crawl all repositories
for repository in repositories:
    try:
        sha = get_sha_for_tag(repository, 'master')
        package = parse_variables(repository, sha, path)
        total_length += package[0]
        total_count += package[1]
    except (Exception) as exc:
        logging.error('\nThis repository has no master branch or doesn\'t exist\n') 
    
stop_time = time.clock()

if total_count > 0:
    total_average = total_length / total_count
    print("\nNumber of variables found for this user: ", total_count)
    print("Average variable length in characters: ", total_average, "\n")
else:
    print("\nNo variables found\n")

elapsed = stop_time - start_time
print("Time elapsed:", elapsed, "seconds")

#winsound.Beep(freq,dur)
input("\nPress \"Enter\" to exit: \n")


