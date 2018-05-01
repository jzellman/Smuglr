Smuglr
======

Smuglr is a tool to download images from SmugMug.  This is useful when you have family and friends that share photos on SmugMug but you'd like to download the photos and albums to your own computer.

If you are interested in this library and plan on signing up with SmugMug. Consider using my referral code: https://secure.smugmug.com/signup.mg?Coupon=5qLwf6TGUTmIk (5qLwf6TGUTmIk). You'll save $5 on your subscription and I'll receive a $10 coupon.

Requirements
----------

Smuglr uses the concurrent.futures standard library to harness all of your CPUs. 
The concurrent.futures library is only available on Python 3.

Usage
----------

    # For now, you'll need to clone the git repo:
    ```
    git clone git://github.com/jzellman/smuglr.git
    cd smuglr
    # print help
    python smuglr.py -h
    # list albums located at someaccount.smugmug.com
    python smuglr.py -a 'someaccount' list-albums
    # list albums located at someaccount.smugmug.com which has a site password of password
    python smuglr.py -a 'someaccount' -p password list-albums
    # sync all albums at someaccount.smugmug.com to ~/Pictures/Smuglr/someaccount/
    python smuglr.py -a 'someaccount' -p password download
    # sync album named Birthday Pictures for account someaccount.smugmug.com to ~/Pictures/Smuglr/someaccount/Birthday Pictures/
    python smuglr.py -a 'someaccount' -p password download --album "Birthday Pictures"
    # sync all albums including the album "Birthday Pictures" which has a password of 'birthday-pictures' and the album
    # "Christmas Pictures" which has a password of 'xmas-pictures'
    python smuglr.py -a 'someaccount' -p password download --albumpass 'Birthday Pictures:birthday-pictures' --albumpass 'Christmas Pictures:xmas-pictures'
    ```

Contributing
------------

Once you've made your commits:

1. [Fork](http://help.github.com/forking/) Smuglr
2. Install requirements listed in test-requirements.txt
3. Run tests: ```pytest```
4. Create a topic branch - `git checkout -b my_branch`
5. Push to your branch - `git push origin my_branch`
6. Create a [Pull Request](http://help.github.com/pull-requests/) from your branch
7. Profit!

