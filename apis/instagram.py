from instabot import Bot
from logs import write_status_log, write_chat_bot, user_options, GET_NAME
from termcolor import cprint, colored
import codecs
import json
import logging
import os.path

try:
    from instagram_private_api import (
        Client, ClientError, ClientLoginError,
        ClientCookieExpiredError, ClientLoginRequiredError,
        __version__ as client_version)
except ImportError:
    import sys
    
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from instagram_private_api import (
        Client, ClientError, ClientLoginError,
        ClientCookieExpiredError, ClientLoginRequiredError,
        __version__ as client_version)


def check_if_following(bot, username) -> bool:
    """
    PRE: All parameters are required
    POST: Check if the current user follows the searched user. It is also used to know if I can access the user's feed
    :param bot: :type object
    :param username: :type string
    :return:
    """
    following = get_follows(bot, False)
    user_info = bot.username_info(username)
    i_following = False
    if user_info['user']['is_private']:
        for users in following['users']:
            if user_info['user']['pk'] in users:
                i_following = True
    else:
        i_following = True
    
    return i_following


def prepare_text(post, post_to_show, attribute, comments, **extra_data) -> tuple:
    """
    PRE: All parameter are required
    POST: A string is formatted which will contain the visual structure of each post
    :param comments:
    :param post:
    :param post_to_show:
    :param attribute:
    :return:
    """
    title = colored(" {}: \n".format(extra_data['text']), 'white', attrs = ['bold'])
    post_to_show += title
    if attribute == "likers":
        count_likes = int(post['like_count'])
        if extra_data['own_feed']:
            if count_likes <= 5:
                for users in post[attribute]:
                    name = users['full_name'] if len(users['full_name']) else users['username']
                    post_to_show += "\t- " + name + '\n'
            else:
                post_to_show += "\t- " + post[attribute][0]['full_name'] + " +{} users \n".format(int(count_likes) - 1)
        else:
            post_to_show += f"\t- total likes: {count_likes} \n"
    else:
        comment_number = 1
        for comment in comments[attribute]:
            text_comment = f"\tNº{comment_number} - " + f"'{comment['text']}'"
            name = comment['user']['full_name'] if len(comment['user']['full_name']) else comment['user']['username']
            post_to_show += text_comment + f" by {name} with {comment['comment_like_count']} likes \n"
            comment_number += 1
    
    return post_to_show, title


def validate_number_post(number, max_number) -> int:
    """
    PRE: All parameters are required
    POST: It is validated that the position of the post within a dictionary exists. And this validated position is returned
    :param number: :type int
    :param max_number: :type int
    :return:
    """
    correct = False
    name = user_options(GET_NAME)
    while not correct:
        if number < 0 or number >= max_number:
            cprint("Number post incorrect", 'red', attrs = ['bold'])
            write_chat_bot("Number post incorrect")
            number = int(input("Enter a valid posting number: "))
            write_chat_bot(number, name)
            write_chat_bot("Enter a valid posting number: ")
        else:
            correct = True
    return number


def show_user_feed(bot, feed, own_feed = False) -> None:
    """
    PRE: All the parameters are required
    POST: The feed of a user chosen by the current user is printed. And it is verified if the feed that is being printed is that of the current user.
    :param bot: :type object
    :param feed: :type dict
    :param own_feed: :type bool
    :return:
    """
    number_post = 1
    post_to_show = ''
    for post in feed:
        comments = bot.media_comments(post['pk'])
        
        indicator_post = colored("\nPost Nº{} \n".format(number_post), 'white', attrs = ['bold', 'underline'])
        title = colored('\n Caption: \n\t', 'white', attrs = ['bold'])
        
        if type(post["caption"]) == dict:
            post_to_show += indicator_post + title + f'"{post["caption"]["text"]}"' + "\n"
        else:
            post_to_show += indicator_post + title + f'' + "\n"
        
        attributes = {'likers': "Likes", 'comments': "Comments"}
        
        for attr, text in attributes.items():
            post_to_show, title = prepare_text(
                post,
                post_to_show,
                attr,
                comments,
                own_feed = own_feed,
                text = text)
        
        number_post += 1
        print(post_to_show)
        write_chat_bot(post_to_show)
        post_to_show = ''


def validate_post_comment(bot, feed, position_comment) -> list:
    """
    PRE: All the parameters cant be null
    POST: The position of the comment x and the post y is validated, and a list with the validated coordinates is returned.
    :param bot:
    :param feed:
    :param position_comment:
    :return:
    """
    correct_post = False
    name = user_options(GET_NAME)
    while not correct_post:
        if not feed[position_comment[0] - 1]:
            text = "The post doesnt exist, please enter a correct post number"
            cprint(text, 'red', attrs = ['bold'])
            write_chat_bot(text)
            position_comment[0] = int(input("Number post: "))
            write_chat_bot(position_comment[0], name)
        else:
            correct_post = True
    
    correct_comment = False
    post = feed[position_comment[0] - 1]
    comments = bot.media_comments(post['pk'])
    
    while not correct_comment:
        if not comments['comments'][position_comment[1] - 1]:
            text = "The comment doesnt exist, please enter a correct comment number"
            cprint(text, 'red', attrs = ['bold'])
            write_chat_bot(text)
            position_comment[1] = int(input("Number comment: "))
            write_chat_bot(position_comment[1], name)
        else:
            correct_comment = True
    
    return position_comment


def my_feed(bot) -> None:
    """
    PRE: The parameter can't be null
    POST: Print current user's feed
    :param bot: :type object
    :return:
    """
    feed = bot.self_feed()['items']
    show_user_feed(bot, feed, own_feed = True)


def post_comment(bot) -> None:
    """
    PRE: The parameter can't be null
    POST: Post a comment on a post from a user chosen by the current user
    :param bot: :type object
    :return:
    """
    name = user_options(GET_NAME)
    are_users = show_search_users(bot, text = 'Who do you want to find to post a comment on his post?')

    while not are_users:
        are_users = show_search_users(bot, "No users with that name were found, please enter a correct name: ")
        write_chat_bot("No users with that name were found, please enter a correct name: ")
        
    username = input("Enter a username: ")
    
    write_chat_bot("Enter a username: ")
    write_chat_bot(username, name)
    
    if bot.username != username:
        can_get_feed = check_if_following(bot, username)
    else:
        can_get_feed = True
    
    if can_get_feed:
        print()


def already_liked(bot, target_id, type_like = 'post') -> bool:
    """
    PRE: The bot and target_id parameter cant be null
    POST: Check if the post / comment is already liked by the current user
    :param bot: :type object
    :param target_id: :type str
    :param type_like: :type str
    :return:
    """
    is_liked = False
    if type_like == 'post':
        likes = bot.media_likers(target_id)['users']
    else:
        likes = bot.comment_likers(target_id)
    
    bot_id = int(bot.authenticated_user_id)
    for likers in likes['users']:
        if bot_id == likers['pk']:
            is_liked = True
    
    return is_liked


def get_id_post(feed, text, edit = False) -> str or int or tuple:
    """
    PRE: The feed and text parameter, cant be null
    POST: Returns the id of the post if the post / comment is not being edited, otherwise, the id of the post and its position in the dictionary will be returned
    :param edit:
    :param text:
    :param feed:
    :return:
    """
    name = user_options(GET_NAME)
    number_post = int(input(f"{text} enter the Nº: ")) - 1
    write_chat_bot(f"{text} enter the Nº: ")
    write_chat_bot(number_post, name)
    number_post = validate_number_post(number_post, len(feed['items']))
    id_post = feed['items'][number_post]['pk']
    
    return id_post if not edit else id_post, number_post


def likes_actions(bot, target_type = "comment", like_type = 'like') -> Exception or ClientError or None:
    """
    PRE: All parameters are required
    POST: Depending on the type of target and type of like, a post or a comment will be liked or unlike
    :param bot: :type object
    :param target_type: :type str
    :param like_type: :type str
    :return:
    """
    name = user_options(GET_NAME)
    try:
        if target_type != "comment":
            are_users = show_search_users(bot, f"Which user do you want to {like_type} the {target_type}? ")
            while not are_users:
                are_users = show_search_users(bot, "No users with that name were found, please enter a correct name: ")
                write_chat_bot("No users with that name were found, please enter a correct name: ")

            write_chat_bot(f"Which user do you want to {like_type} the {target_type}? \n Enter username: ")
            username = input("Enter username: ")
            write_chat_bot(username, name)
            
            can_get_feed = check_if_following(bot, username)
            if can_get_feed:
                feed = bot.username_feed(username)['items']
                feed_not_empty = feed[0]
                if feed_not_empty:
                    own_feed = username == bot.username
                    show_user_feed(bot, feed, own_feed = own_feed)
                    id_post = get_id_post(feed = feed, text = f"Which post would you {like_type} to post a like?")
                    if like_type == 'like':
                        like(bot, id_post)
                    else:
                        unlike(bot, id_post)
                else:
                    cprint("The user has no posts\n", 'red', attrs = ['bold', 'underline'])
            else:
                cprint(f"You cannot access the feed of the user {username} because it is a private account that you do not follow, or because it has blocked you\n", 'red',
                       attrs = ['bold', 'underline'])
        else:
            cprint("Your feed: ", 'blue', attrs = ['bold'])
            feed = bot.self_feed()
            show_user_feed(bot, feed['items'], own_feed = True)
            feed_not_empty = feed['items'][0]
            if feed_not_empty:
                text = f"Which comment would you like to post a {like_type}?"
                comment_data = prepare_comment(bot = bot, feed = feed['items'], text = text)
                if like_type == 'like':
                    like(bot, comment_data["comment_id"], target_type = 'comment', comment_text = comment_data['comment_text'])
                else:
                    unlike(bot, comment_data["comment_id"], target_type = 'comment')
            else:
                cprint("Your feed is empty", 'red', attrs = ['bold'])
    
    except Exception as error:
        raise Exception(error)


def prepare_comment(bot, feed, text) -> dict or ClientError:
    """
    PRE: All the parameters are required
    POST: The position of x comment is validated and a dictionary is prepared containing the id of the post, the id of the comment, and the comment text
    :param bot:
    :param feed:
    :param text:
    :return: :type dict or ClientError
    """
    name = user_options(GET_NAME)
    position_comment = input(f"{text} enter the post number and comment number. Ej: 1, 2 : ").split(',')
    position_comment = [int(x.strip()) for x in position_comment]
    
    write_chat_bot(f"{text} enter the post number and comment number. Ej: 1, 2 : ")
    write_chat_bot(position_comment, name)
    
    position_comment = validate_post_comment(bot, feed, position_comment)
    post_id = feed[position_comment[0] - 1]['pk']
    comments = bot.media_comments(post_id)['comments']
    comment_id = comments[position_comment[1] - 1]['pk']
    comment_text = comments[position_comment[1] - 1]['text']
    
    return {'post_id': post_id, 'comment_id': comment_id, 'comment_text': comment_text}


def unlike(bot, target_id, target_type = 'post') -> None or ClientError:
    """
    PRE: Bot parameters and target_id can't be null
    POST: Depending on the type of target, a post or a comment is unliked. The target_id corresponds to the id of a comment or a post.
    :param bot:
    :param target_id:
    :param target_type:
    :return:
    """
    
    if target_type == 'post':
        result = bot.delete_like(target_id)
    else:
        result = bot.comment_unlike(target_id)
    
    if result['status'] == 'ok':
        cprint(f"The {target_type} is unliked correctly!\n", 'green', attrs = ['bold'])
    else:
        cprint(f"There was a problem disliking the {target_type}, please try again later!\n", 'red', attrs = ['bold'])


def like(bot, target_id, target_type = 'post', comment_text = '') -> None or ClientError:
    """
    PRE: Bot parameters and target_id can't be null
    POST: Depending on the type of target, a post or a comment is liked. The target_id corresponds to the id of a comment or a post.
    :param bot: :type object
    :param target_id: :type str
    :param target_type: :type str
    :param comment_text: :type str
    :return:
    """
    name = user_options(GET_NAME)
    if not already_liked(bot, target_id, target_type):
        if target_type == 'post':
            result = bot.post_like(media_id = target_id)
        else:
            result = bot.comment_like(comment_id = target_id)
        
        if result['status'] == 'ok':
            text = "It has been liked correctly!\n" if target_type == 'post' else f"The comment '{comment_text}' has been liked correctly"
            cprint(text, 'green', attrs = ['bold'])
            write_chat_bot(text)
        else:
            cprint(f"There was a problem liking the {target_type}, try again later!\n", 'red', attrs = ['bold', 'underline'])
            write_chat_bot(f"There was a problem liking the {target_type}, try again later!")
    else:
        do_unlike = input(f"The {target_type} is already liked by you, you want to unliked? (yes/no): ".lower()) in ['yes', 'ye', 'y']
        write_chat_bot(f"The {target_type} is already liked by you, you want to unliked? (yes/no): ")
        write_chat_bot(do_unlike, name)
        if do_unlike:
            unlike(bot, target_id, target_type)
        else:
            print("The like has been left as it was\n")
            write_chat_bot("The like has been left as it was")


def edit_profile(bot) -> Exception or ClientError or None:
    """
    PRE: The parameter can't be null
    POST: The attributes available to change from the user's profile are printed,
          a dictionary will be prepared with the data to be changed, and the change will be made in the profile
    :param bot: :type object
    :return:
    """
    my_profile = bot._call_api('accounts/current_user/', query = {'edit': 'true'})
    text_to_log = "Your actual profile is: \n"
    genders = ['male', 'female', 'unspecified']
    print(text_to_log)
    attributes = {
        'Full name': 'full_name',
        'Private account': 'is_private',
        'Biography': 'biography',
        'External url': 'external_url',
        'Email': 'email',
        'Phone number': 'phone_number',
        'Gender': 'gender',
    }
    
    data_change = {}
    all_data = ''
    profile = my_profile['user']
    
    for key, attribute in attributes.items():
        if attribute == 'gender':
            all_data += f'{key} : {genders[int(profile[attribute])]}\n'
        else:
            all_data += f'{key} : {profile[attribute]}\n'
    
    print(all_data)
    text_to_log += all_data
    prepare_profile(profile, attributes, data_change, genders)
    
    write_chat_bot(text_to_log)
    
    try:
        status_account = bot.set_account_private() if data_change['is_private'] else bot.set_account_public()
        result = bot.edit_profile(
            first_name = data_change['full_name'],
            biography = data_change['biography'],
            external_url = data_change['external_url'],
            email = data_change['email'],
            gender = int(data_change['gender']),
            phone_number = data_change['phone_number']
        )
        if result['result'] == 'ok' and status_account['status'] == 'ok':
            text = "Profile has been modified successfully!"
            write_chat_bot(text)
            cprint(text, 'green', attrs = ['bold'])
        else:
            text = "There was a problem updating the profile, please try again"
            write_chat_bot(text)
            cprint(text, 'red', attrs = ['bold'])
    
    except Exception as error:
        write_status_log(error, 'Failed')
        raise Exception(error)


def prepare_profile(profile, attributes, data_change, genders) -> None:
    """
    PRE: All parameters are required
    POST: The "data_change" dictionary is prepared with the information to change or maintain, of the current user's profile
    :param profile: :type dict
    :param attributes: :type dict
    :param data_change: :type dict
    :param genders: :type list
    :return:
    """
    name = user_options(GET_NAME)
    for key, attribute in attributes.items():
        if attribute == 'full_name':
            cprint("IMPORTANT!", 'red', attrs = ['bold', 'blink'])
            cprint(
                "If you have changed the full name 2 times within a period of 14 days, you will not be able to modify your full name, just leave it empty, the program will not be able to change the full name.\n Be aware of your decision",
                'red',
                attrs = ['bold'])
            write_chat_bot(
                "IMPORTANT! \n If you have changed the full name 2 times within a period of 14 days, you will not be able to modify your full name, just leave it empty, the program will not be able to change the full name.\n Be aware of your decision")
        
        change_attribute = input(f"Do you want to change {key}? yes/no: ".lower()) in ['yes', 'y', 'ye']
        
        write_chat_bot(f"Do you want to change {key}? yes/no: ")
        write_chat_bot(change_attribute, name)
        
        if change_attribute:
            if attribute == 'is_private':
                print("To change your account from private to public or vice versa, enter public/private")
                write_chat_bot(f"To change your account from private to public or vice versa, enter public/private")
            elif attribute == 'gender':
                print("To change your gender, enter male/female/unspecified")
                write_chat_bot(f"To change your gender, enter male/female/unspecified")
            
            new_data = input(f"Enter the new value for {key}: ")
            
            write_chat_bot(f"Enter the new value for {key}: ")
            write_chat_bot(new_data, name)
            
            secure = input(f"Are you sure to change {key} to '{new_data}'? yes/no: ".lower()) in ['yes', 'y', 'ye']
            
            write_chat_bot(f"Are you sure to change {key} to '{new_data}'? yes/no: ")
            write_chat_bot(secure, name)
            
            if secure:
                if attribute == 'is_private':
                    new_data = True if new_data.lower() in ['private', 'priv', 'p'] else False
                elif attribute == 'gender':
                    if new_data in genders:
                        new_data = int(genders.index(new_data)) + 1
                    else:
                        while new_data not in genders:
                            new_data = input("The gender you have selected does not correspond to those available (male / female / unspecified), please enter a valid one: ")
                            
                            write_chat_bot("The gender you have selected does not correspond to those available (male / female / unspecified), please enter a valid one: ")
                            write_chat_bot(new_data, name)
                        
                        else:
                            new_data = int(genders.index(new_data)) + 1
                
                data_change[attribute] = new_data
            else:
                print(f"No changes have been made to the {key}")
                write_chat_bot(f"No changes have been made to the {key}")
        else:
            data_change[attribute] = profile[attribute]


def delete(bot, target_id, target_type, parent_id = '') -> None or Exception:
    """
    PRE: Bot parameters, target_id, and target type cannot be null
    POST: Depending on the type of target, a post or a comment is deleted. The target_id corresponds to the id of a comment or a post.
          The parent_id is only used if the target type is a comment and its value refers to the id of the post in which the comment is found.
    :param bot: :type object
    :param target_id: :type str
    :param target_type: :type str
    :param parent_id: :type str
    :return: None or Exception
    """
    
    if target_type == 'post':
        result = bot.delete_media(media_id = str(target_id))
    else:
        result = bot.delete_comment(post_id = str(parent_id), comment_id = str(target_id))
    
    if result['status'] == 'ok':
        cprint(f"The {target_type} has been successfully removed!\n", 'green', attrs = ['bold'])
        write_chat_bot(f"The {target_type} has been successfully removed!")
    else:
        cprint(f"The {target_type} could not be removed. Please try again later\n", 'red', attrs = ['bold'])
        write_chat_bot(f"The {target_type} could not be removed. Please try again later")


def edit_post_actions(bot, edit_type, target_type = 'post'):
    """
    PRE: Bot parameters and type_edit cannot be null
    POST: A user post will be edited or deleted. As you can also delete a comment from said post
    :param bot: :type object
    :param edit_type: :type str
    :param target_type: :type str
    :return:
    """
    feed = bot.self_feed()
    is_feed_empty = feed['items'][0]
    name = user_options(GET_NAME)
    if is_feed_empty:
        show_user_feed(bot, feed['items'], own_feed = True)
        if target_type == 'post':
            id_post, number_post = get_id_post(feed, text = f"Which post would you {edit_type}?", edit = True)
            if edit_type == 'edit':
                cprint("You can only edit the caption!\n", 'blue', attrs = ['bold', 'blink'])
                write_chat_bot("You can only edit the caption!")
                
                old_caption = feed['items'][number_post]['caption']['text']
                new_caption = input("Enter the new caption: ")
                secure = input(f"\nAre you sure to change '{old_caption}' to '{new_caption}'? (yes/no): ") in ['yes', 'ye', 'y']
                
                write_chat_bot(f"Are you sure to change '{old_caption}' to '{new_caption}'? (yes/no): ")
                write_chat_bot(secure, name)
                
                if secure:
                    id_post = feed['items'][number_post]['pk']
                    result = bot.edit_media(media_id = id_post, caption = new_caption)
                    if result['status'] == 'ok':
                        cprint("It has been edited successfully!\n", 'green', attrs = ['bold'])
                        write_chat_bot("It has been edited successfully!")
                    
                    else:
                        cprint("An error occurred while changing it, please try again later\n", 'red', attrs = ['bold'])
                        write_chat_bot("An error occurred while changing it, please try again later")
                else:
                    cprint("The post has not been modified\n", 'blue', attrs = ['bold'])
                    write_chat_bot("The post has not been modified")
            
            else:
                secure = input(f"Are you sure to {edit_type} the post? (yes/no): \n") in ['yes', 'ye', 'y']
                write_chat_bot(f"Are you sure to {edit_type} the post? (yes/no): ")
                write_chat_bot(secure, name)
                
                if secure:
                    id_post = feed['items'][number_post]['pk']
                    delete(bot, id_post, 'post')
        else:
            if edit_type == 'edit':
                cprint("You cannot edit a comment, only delete it\n", 'blue', attrs = ['bold', 'underline'])
                write_chat_bot(f"You cannot edit a comment, only delete it")
            
            secure_delete = input("Do you want to delete a comment from a post? (yes/no): \n") in ['yes', 'ye', 'y']
            write_chat_bot("Do you want to delete a comment from a post? (yes/no):")
            write_chat_bot(secure_delete, name)
            
            if secure_delete:
                text = "Which comment would you delete?"
                comment_data = prepare_comment(bot = bot, feed = feed['items'], text = text)
                delete(bot, comment_data['comment_id'], 'comment', comment_data['post_id'])
    else:
        cprint("Your feed is empty", 'red', attrs = ['bold'])
        write_chat_bot("Your feed is empty")


def follow_actions(bot, follow_type = 'follow') -> Exception or ClientError or None:
    """
    PRE: The bot parameter can't be null
    POST: If the type of follow is "unfollow", the user's current followers are printed, and they are given to choose who they want to unfollow.
          Otherwise, let the type be "follow", a query is made based on a name entered by the user, and will choose who to follow
    :param bot: :type object
    :param follow_type: :type str
    :return:
    """
    try:
        if follow_type != 'follow':
            results = get_follows(bot)
            username = input(f"Who do you want to {follow_type}? ")
            for user in results['users']:
                if user['username'] == username:
                    if bot.friendships_destroy(user['pk']):
                        text = f"{username} has been successfully unfollowed!"
                        cprint(text, 'green', attrs = ['bold'])
                        write_chat_bot(text)
        else:
            show_search_users(bot)
            username = input(f"Who do you want to {follow_type}? ")
            user = bot.username_info(username)['user']
            user_id = user['pk']
            if bot.friendships_create(user_id = user_id):
                text = f"{username} has a private account, we have sent him a request with success!" if user['is_private'] else f"{username} has been followed with success!"
                write_chat_bot(text)
                cprint(text, 'green', attrs = ['bold'])
            else:
                text = "There was a problem performing the action, please try again"
                cprint(text, 'red', attrs = ['bold'])
                write_chat_bot(text)
    
    except Exception as error:
        write_status_log(error, 'Internal server error')
        raise Exception(error)


def get_follows(bot, show = True, follow_type = 'following') -> dict or list:
    """
    PRE: The bot parameter can't be null
    POST: If the show parameter is true the followers of the current user are printed or the users followed by the current user are printed,
          depending on the value of the type_show parameter which can be "following" or "followers"
    :param bot:
    :param show:
    :param follow_type:
    :return:
    """
    rank = bot.generate_uuid()
    user_id = bot.authenticated_user_id
    if follow_type == 'following':
        results = bot.user_following(user_id, rank)
        text = "You are following: \n"
    else:
        results = bot.user_followers(user_id, rank)
        text = "Your followers: \n"
    
    if show:
        cprint(text, 'blue', attrs = ['bold', 'underline'])
        for user in results['users']:
            print(f"{user['username']} \n")
    
    return results


def show_search_users(bot, text = 'Who do you want to search?') -> None or ClientError:
    """
    PRE: The bot parameter can't be null
    POST: Found users based on a name are printed. And the text parameter varies because different texts are used to search, like, follow, etc.
    :param bot: :type object
    :param text: :type str
    :return:
    """
    name = user_options(GET_NAME)
    query = input(text)
    write_chat_bot(text)
    write_chat_bot(query, name)
    
    results = bot.search_users(query = query)
    text_to_log = "The users found are \n"
    if results['num_results'] > 0:
        print(text_to_log)
        for user in results['users']:
            full_data = ''
            full_data += f"{user['username']} {'Its a private profile' if user['is_private'] else 'Its a public profile'}"
            if 'social_context' in user.keys():
                full_data += f" Someone you know follows this account: {user['social_context']}"
            if user['friendship_status']['following']:
                full_data += colored(f" You are currently following it", 'green')
            
            print(full_data + "\n")
            text_to_log += full_data + '\n'
        write_chat_bot(text_to_log)
        are_users = True
    else:
        are_users = False
        print("No user with that name was found \n")
        write_chat_bot("No user with that name was found")
    
    return are_users


def show_last_messages(last_messages, bot_id) -> None:
    """
    PRE: Both parameters are required and cannot be empty
    POST: If the user has chats with other users, the last event of each chat will be printed.
          And the bot_id is used to know if the current user was the one who made the last chat event
    :param bot_id: :type str
    :param last_messages: :type dict
    :return:
    """
    text_show = ''
    message_number = 1
    title = colored('Messages: \n', 'white', attrs = ['bold'])
    text_show += title
    message = ''
    text_to_bot = 'Messages: \n'
    empty_messages = last_messages['threads']
    if not empty_messages:
        for conversations in last_messages['threads']:
            user = conversations['users'][0]['full_name']
            text_show += colored(f"\t-Nº{message_number} - {user}: \n", 'white', attrs = ['bold'])
            text_to_bot += f"\t-Nº{message_number} - {user}: \n"
            i_sent = conversations['items'][0]['user_id'] == int(bot_id)
            its_me = "You sent" if i_sent else "He sent"
            
            if conversations['items'][0]['item_type'] == 'media':
                message += f"\t\t-({its_me}) Its a image, url: " + f"{conversations['items'][0]['media']['image_versions2']['candidates'][0]['url']} \n"
            
            elif conversations['items'][0]['item_type'] == 'text':
                message += f"\t\t-({its_me}) Text: {conversations['items'][0]['text']}\n"
            
            elif conversations['items'][0]['item_type'] == 'media_share':
                image = conversations['items'][0]['media_share']['image_versions2']['candidates'][0]['url']
                user_post = conversations['items'][0]['media_share']['users']['username']
                caption = conversations['items'][0]['media_share']['caption']['text']
                url_post = f"https://instagram.com/p/{conversations['items'][0]['media_share']['code']}/"
                message += f"\t\t-({its_me}) It is a publication \n From :{user_post} \n Url: {url_post} \n Image: {image} \n Caption: '{caption}' \n"
            
            elif conversations['items'][0]['item_type'] == 'profile':
                username = conversations['items'][0]['media_share']['users'][0]['username']
                url_post = f"https://instagram.com/{username}/"
                message += f"\t\t-({its_me}) It is a profile \n Url: {url_post} \n"
            
            elif conversations['items'][0]['item_type'] == 'placeholder':
                message += f"\t\t-({its_me}) It is a reel, please open it on the cell phone\n"
            
            elif conversations['items'][0]['item_type'] == 'action_log':
                message += f"\t\t-({its_me}) It is a action, {conversations['items'][0]['action_log']['description']} \n"
            
            text_show += message
            text_to_bot += message
            write_chat_bot(text_to_bot)
            
            message = ''
            message_number += 1
        
        print(text_show)
    else:
        cprint("You don't have any chat\n", 'red', ['bold'])
        write_chat_bot("You don't have any chat")


def message_actions(bot, action_type = 'send') -> None or Exception or ClientError:
    """
    PRE: The parameters are required
    POST: If the action type is "send", a message will be sent to a user determined by the current user.
          In the opposite case that the action is not "send" which would be "get", the last events of each chat will be shown
    :param bot: :type Object
    :param action_type: :type str
    :return:
    """
    name = user_options(GET_NAME)
    cprint("IMPORTANT!!\n", 'red', attrs = ['bold', 'blink', 'underline'])
    cprint("Thanks to Mark Zuckerberg, we can only show the latest events from each chat.\nWhether it is a like to a comment, share a profile / reel / publication / a message\n", 'red',
           attrs = ['bold', 'underline'])
    write_chat_bot("IMPORTANT!!\n Thanks to Mark Zuckerberg, we can only show the latest events from each chat.\nWhether it is a like to a comment, share a profile / reel / publication / a message")
    try:
        if action_type != 'send':
            last_messages = bot.direct_v2_inbox()['inbox']
            show_last_messages(last_messages, bot.authenticated_user_id)
        else:
            cprint("Please wait a few seconds\n", 'blue', attrs = ['bold'])
            write_chat_bot("Please wait a few seconds")
            
            aux_api = connection_aux_api(bot.username, bot.password)
            are_users = show_search_users(bot, "Who do you want to send a message to? ")
            
            while not are_users:
                are_users = show_search_users(bot, "No users with that name were found, please enter a correct name: ")
                write_chat_bot("No users with that name were found, please enter a correct name: ")
                
            username = input("Please enter username: ")
            text = input("Message: ")
            
            write_chat_bot("Please enter username: ")
            write_chat_bot(username, name)
            write_chat_bot("Message: ")
            write_chat_bot(text, name)
            
            user_info = bot.username_info(username)
            result = aux_api.send_message(text, str(user_info['user']['pk']))
            if result:
                cprint(f"The message has been sent to {username} correctly!\n", 'green', attrs = ['bold'])
                write_chat_bot(f"The message has been sent to {username} correctly!")
            else:
                cprint(f"The message was not sent to {username} correctly, please try again later\n", 'red', attrs = ['bold'])
                write_chat_bot(f"The message was not sent to {username} correctly, please try again later")
    
    except Exception as error:
        raise Exception(error)


# ------------ CONNECTIONS AND CREDENTIALS ---------------#

def to_json(python_object) -> dict:
    """
    
    :param python_object:
    :return:
    """
    if isinstance(python_object, bytes):
        return {'__class__': 'bytes',
                '__value__': codecs.encode(python_object, 'base64').decode()}
    raise TypeError(repr(python_object) + ' is not JSON serializable')


def from_json(json_object):
    """
    
    :param json_object:
    :return:
    """
    if '__class__' in json_object and json_object['__class__'] == 'bytes':
        return codecs.decode(json_object['__value__'].encode(), 'base64')
    return json_object


def on_login_callback(api, new_settings_file) -> None:
    """
    PRE: The api and the file that saves the settings cannot be empty
    POST: Write, in a json, the cookies and settings to avoid re-login
    :param api: the actual Client object
    :param new_settings_file: The json file where the credentials will be saved
    :return:
    """
    cache_settings = api.settings
    try:
        with open(new_settings_file, 'w') as outfile:
            json.dump(cache_settings, outfile, default = to_json)
    except Exception as error:
        write_status_log(error, 'failed')
        raise Exception(error)


def connection_instagram(username = 'crux.bot', password = 'crux123') -> object:
    """
    PRE: If the user does not give us the credentials of their instagram user, we will use the crux data
    POST: Credentials are created to avoid re-logging, and the connection with the api is created
    :param username: :type str
    :param password: :type str
    :return: object
    """
    device_id = None
    try:
        settings_file = os.path.abspath('credentials/instagram_api.json')
        if not os.path.isfile(settings_file):
            # If the credentials do not exist, do a new login
            insta_bot = Client(
                username, password,
                on_login = lambda x: on_login_callback(x, settings_file))
        else:
            # If the credentials do not exist, do a new login
            try:
                with open(settings_file) as file_data:
                    cached_settings = json.load(file_data, object_hook = from_json)
            except Exception as error:
                write_status_log(error, 'failed')
                raise Exception(error)
            
            print('Reusing settings: {0!s} \n'.format(settings_file))
            
            device_id = cached_settings.get('device_id')
            insta_bot = Client(
                username, password,
                settings = cached_settings)
    
    except (ClientCookieExpiredError, ClientLoginRequiredError) as e:
        # Credentials expired
        # It does a re login but using ua, keys and such
        insta_bot = Client(
            username, password,
            device_id = device_id,
            on_login = lambda x: on_login_callback(x, settings_file))
    
    except ClientLoginError as e:
        write_status_log(e, 'ClientLoginError')
        raise ClientLoginError(e)
    except ClientError as e:
        write_status_log('ClientError {0!s} (Code: {1:d}, Response: {2!s})'.format(e.msg, e.code, e.error_response), 'ClientError')
        raise ClientError('ClientError {0!s} (Code: {1:d}, Response: {2!s})'.format(e.msg, e.code, e.error_response))
    except Exception as e:
        write_status_log('Unexpected Exception: {0!s}'.format(e), 'Exception')
        raise Exception('Unexpected Exception: {0!s}'.format(e))
    
    write_status_log('You have successfully connected with the instagram!')
    write_chat_bot('You have successfully connected with the instagram!')
    cprint("You have successfully connected with the instagram! \n", 'green', attrs = ['bold'])
    
    return insta_bot


def connection_aux_api(username, password) -> object:
    """
    This connection is made specifically for sending messages
    PRE: The username and password must not be empty, and represent the username and password of the current user
    POST: Generates the connection with the api, and returns its object
    :param username: :type: str
    :param password: :type: str
    :return:
    """
    aux_api = ''
    try:
        logging.disable(logging.CRITICAL)
        aux_api = Bot()
        aux_api.login(username = username, password = password, use_cookie = False)
    
    except (KeyboardInterrupt, EOFError, SystemExit):
        aux_api.logout()
    
    except Exception as error:
        raise Exception(error)
    
    write_status_log('You have successfully connected with the aux api')
    
    return aux_api