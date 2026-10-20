[33m4fb57a7[m[33m ([m[1;36mHEAD[m[33m -> [m[1;32mmain[m[33m, [m[1;31mHotel-Booking/main[m[33m, [m[1;31mHotel-Booking/HEAD[m[33m)[m HEAD@{0}: undo: checkout: moving from main to main
[33m4fb57a7[m[33m ([m[1;36mHEAD[m[33m -> [m[1;32mmain[m[33m, [m[1;31mHotel-Booking/main[m[33m, [m[1;31mHotel-Booking/HEAD[m[33m)[m HEAD@{1}: checkout: moving from main to main
[33m4fb57a7[m[33m ([m[1;36mHEAD[m[33m -> [m[1;32mmain[m[33m, [m[1;31mHotel-Booking/main[m[33m, [m[1;31mHotel-Booking/HEAD[m[33m)[m HEAD@{2}: branch: Reset to 4fb57a7aea7eedd06272790988bda523564ac839
[33ma79ba9a[m HEAD@{3}: merge Hotel-Booking/main: Merge made by the 'ort' strategy.
[33md091659[m HEAD@{4}: commit: Making the website responsive
[33mb1a2395[m HEAD@{5}: discard: [4c14a38f34dc3b38fe4b09eed9e94ef1d9e1b196]
[33mb1a2395[m HEAD@{6}: commit: fix UI bug
[33m736dc48[m HEAD@{7}: commit: dockerizing project
[33m5b56640[m HEAD@{8}: discard: [df1c2d24bdfe8cfc3b20435edd69de8839f0032c]
[33m5b56640[m HEAD@{9}: commit: write test views for reservations app
[33mf5de00b[m HEAD@{10}: commit: write test models for reservations app
[33md8b7e2d[m HEAD@{11}: commit: write test views for hotels app
[33m112b29c[m HEAD@{12}: commit: write test forms for hotels app
[33m58115bb[m HEAD@{13}: commit: write test models for hotels app
[33m1c73c1f[m HEAD@{14}: commit: write test for accounts app
[33md79bd2e[m HEAD@{15}: commit: show top review in home page
[33m93e84d8[m HEAD@{16}: commit: create system contact us
[33m79ce4f2[m HEAD@{17}: commit: debugging
[33mc371c20[m HEAD@{18}: discard: [86213767697e409fa797a6fd3067ca93c85f1467]
[33mc371c20[m HEAD@{19}: commit: create system filter rooms
[33mfbe423e[m HEAD@{20}: commit: change alert style
[33m295bccf[m HEAD@{21}: discard: [ffe66cad7cfdd6b0db01c471bad5b11a4dede695]
[33m295bccf[m HEAD@{22}: discard: [23f8e240eee1630bb449d913a7b5d85e2402d227]
[33m295bccf[m HEAD@{23}: commit: add system show reserved room
[33m81ea5ea[m HEAD@{24}: commit: debugging
[33m6853750[m HEAD@{25}: commit: error handling for redirect user to payment getaway
[33me86c3f7[m HEAD@{26}: commit: page for payment fail and success
[33m2c34be5[m HEAD@{27}: commit: create system reservations and payment-getaway
[33m6b2c28e[m HEAD@{28}: commit: create reservation app
[33m6f546d6[m HEAD@{29}: commit: change header
[33m9a8c4f6[m HEAD@{30}: commit (amend): debugging
[33m44108ec[m HEAD@{31}: commit: debigging
[33meec36ff[m HEAD@{32}: commit: add another system
[33meaa8a94[m HEAD@{33}: commit: change homepage template
[33mac1d31e[m HEAD@{34}: discard: [6e1b88a0c6e4520acef940fc34366da4d5b7004b]
[33mac1d31e[m HEAD@{35}: commit (amend): search sidebar
[33m78f0ea6[m HEAD@{36}: commit: search sidebsar
[33mc67acf7[m HEAD@{37}: discard: [da60847608c694980eb44a16d2609e4385e1df07]
[33mc67acf7[m HEAD@{38}: discard: [2c0a6b143f6b894deae874bb48c36e8e5e43303e]
[33mc67acf7[m HEAD@{39}: commit: add Booking model, add jalali calendar
[33m913c683[m HEAD@{40}: discard: [8d8d0dee267030948613f8dda2e86969a848184a]
[33m913c683[m HEAD@{41}: commit: add requirements.txt file
[33m57018a6[m HEAD@{42}: commit: change admin panel to persian
[33m2d9b88e[m HEAD@{43}: commit: add system delete review
[33mc2964b5[m HEAD@{44}: commit: modal for delete review
[33m57bbf13[m HEAD@{45}: commit: add system add review
[33m9b2e19b[m HEAD@{46}: commit: create system show reviews
[33m2845a80[m HEAD@{47}: commit: change template of room detail
[33mb689cf4[m HEAD@{48}: commit: add room detail template
[33m4a0f8b8[m HEAD@{49}: commit: add user profile view
[33m2a6848c[m HEAD@{50}: commit: debugging and add modal for messages
[33m54f597f[m HEAD@{51}: commit: template for show rooms
[33m772e584[m HEAD@{52}: commit: add home page and show rooms
[33m06b4e84[m HEAD@{53}: commit: create system signUp and signIn
[33m8566ef3[m HEAD@{54}: commit: add static files
[33m487a13d[m HEAD@{55}: rebase (finish): returning to refs/heads/main
[33m487a13d[m HEAD@{56}: rebase (pick): create project
[33mf427aae[m HEAD@{57}: rebase (start): checkout Hotel-Booking/main
[33mfbe1846[m HEAD@{58}: Branch: renamed refs/heads/master to refs/heads/main
[33mfbe1846[m HEAD@{60}: commit (initial): create project
[33mcommit d0916598963cf46240c5715253101b6911e5ffd9[m
Author: Abolfazl <dge51547@gmail.com>
Date:   Fri Oct 2 11:49:03 2026 +0330

    Making the website responsive

 accounts/templates/accounts/otp_verify.html        |   14 [32m+[m
 accounts/templates/accounts/profile.html           |   12 [32m+[m[31m-[m
 accounts/templates/accounts/singIn_singUp.html     |   14 [32m+[m
 hotels/templates/hotels/index.html                 |   24 [32m+[m[31m-[m
 hotels/templates/hotels/room_detail.html           |    2 [32m+[m[31m-[m
 pages/templates/pages/contact_us.html              |   14 [32m+[m[31m-[m
 public/static/css/responsive.css                   | 1571 [32m++++++++++++++++++++[m
 .../templates/reservations/payment_fail.html       |   49 [32m+[m
 .../templates/reservations/payment_success.html    |   85 [32m++[m
 static/css/responsive.css                          | 1571 [32m++++++++++++++++++++[m
 templates/includes/footer.html                     |   40 [32m+[m[31m-[m
 templates/includes/head_references.html            |    1 [32m+[m
 templates/includes/header.html                     |   42 [32m+[m[31m-[m
 13 files changed, 3396 insertions(+), 43 deletions(-)
