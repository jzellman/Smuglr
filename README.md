Smugler
======

Smugler is a Python library that contains a lightweight (depends on Python standard lib only) API for retrieving photos and albums from SmugMug and a tool (smugler.py) for syncing SmugMug albums to your computer. This is useful when you have family and friends that share photos on SmugMug but you'd like to download the photos and albums to your own computer.

If you are interested in this library and plan on signing up with SmugMug. Consider using my referral code: https://secure.smugmug.com/signup.mg?Coupon=5qLwf6TGUTmIk (5qLwf6TGUTmIk). You'll save $5 on your subscription and I'll receive a $10 coupon. 

Usage
----------

    # For now, you'll need to clone the git repo:
    git clone git://github.com/jzellman/smugler.git
    cd smugler
    # print help
    python smugler.py -h
    # list albums located at someaccount.smugmug.com
    python smugler.py albums -a 'someaccount'
    # list albums located at someaccount.smugmug.com which has a site password of password
    python smugler.py albums -a 'someaccount' -p password
    # sync all albums at someaccount.smugmug.com to ~/Pictures/Smugler/someaccount/
    python smugler.py sync -a 'someaccount' -p password
    # sync album named Birthday Pictures for account someaccount.smugmug.com to ~/Pictures/Smugler/someaccount/Birthday Pictures/
    python smugler.py sync-album -a 'someaccount' -p password "Birthday Pictures"
    
Contributing
------------

Once you've made your commits:

1. [Fork](http://help.github.com/forking/) Smugler
2. Create a topic branch - `git checkout -b my_branch`
3. Push to your branch - `git push origin my_branch`
4. Create a [Pull Request](http://help.github.com/pull-requests/) from your branch
5. Profit! 

