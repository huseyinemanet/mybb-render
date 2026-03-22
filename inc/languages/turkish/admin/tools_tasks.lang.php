<?php
/**
 * MyBB 1.8 Turkish Language Pack
 * Copyright 2014 MyBB Group, All Rights Reserved
 *
 * Turkish Translation: mybbturkce.com
 * Copyright ©  All Rights Reserved
 * Last Edit: 05.11.2016 / 15:19 - ( )
 */

$l['task_manager'] = "Zamanlanmış Görevleri Yönet";
$l['add_new_task'] = "Yeni Görev Ekle";
$l['add_new_task_desc'] = "Bu kısımdan, forumunuzda otomatik olarak çalıştırılmasını istediğiniz yeni bir zamanlanmış görev oluşturabilirsiniz.";
$l['edit_task'] = "Görevi Düzenle";
$l['edit_task_desc'] = "Bu kısımdan, zamanlanmış görevin çeşitli ayarları düzenleyebilirsiniz.";
$l['task_logs'] = "Görev Kayıtları";
$l['view_task_logs'] = "Görev Kayıtları";
$l['view_task_logs_desc'] = "Görev çalıştığında ve kayıt aktif olduğunda, sonuçlar ya da hatalar aşağıda listelenecektir. 30 Günden eski girişler otomatik olarak silinecektir.";
$l['scheduled_tasks'] = "Zamanlanmış Görevler";
$l['scheduled_tasks_desc'] = "Bu kısımdan, forumunuzda otomatik olarak çalışacak görevleri yönetebilirsiniz. Ayrıca bir görevi hemen çalıştırmak için görevin sağındaki, <img src=\"../admin/styles/default/images/icons/run_task.png\" style=\"vertical-align: middle;\" width=\"15\" height=\"15\" alt=\"\" border=\"0\">  (saat) simgesine tıklayın.";

$l['title'] = "Görev Başlığı";
$l['short_description'] = "Kısa Bilgi";
$l['task_file'] = "Görev Dosyası";
$l['task_file_desc'] = "Çalıştırmak ya da oluşturmak istediğiniz görev dosyasını seçin.";
$l['time_minutes'] = "Zamanlama Ayarı: <span style=\"color: rgb(128, 0, 0);\">Belirli Dakikalar</span>";
$l['time_minutes_desc'] = "Bu görevin berlirli dakikalarda çalışması için <strong>(0-59)</strong> arası belirleyeceğiniz dakikaları virgül ile ayırarak giriniz.<br /> Eğer, metin kutusuna sadece <strong>'*'</strong> yıldız simgesini yazarsanız, bu görev her dakika başı çalışacaktır.";
$l['time_hours'] = "Zamanlama Ayarı: <span style=\"color: rgb(128, 0, 0);\">Belirli Saatler</span>";
$l['time_hours_desc'] = "Bu görevin berlirli saatlerde çalışması için <strong>(0-23)</strong> arası belirleyeceğiniz saatleri virgül ile ayırarak giriniz.<br /> Eğer, metin kutusuna sadece <strong>'*'</strong> yıldız simgesini yazarsanız, bu görev her saat başı çalışacaktır.";
$l['time_days_of_month'] = "Zamanlama Ayarı: <span style=\"color: rgb(128, 0, 0);\">Belirli Günler</span>";
$l['time_days_of_month_desc'] = "Bu görevin berlirli günlerde çalışması için <strong>(1-31)</strong> arası belirleyeceğiniz günleri virgül ile ayırarak giriniz.<br /> Eğer, metin kutusuna sadece <strong>'*'</strong> yıldız simgesini yazarsanız, bu görev her gün çalışacaktır.";
$l['every_weekday'] = "Her İş Günü";
$l['sunday'] = "Pazar";
$l['monday'] = "Pazartesi";
$l['tuesday'] = "Salı";
$l['wednesday'] = "Çarşamba";
$l['thursday'] = "Perşembe";
$l['friday'] = "Cuma";
$l['saturday'] = "Cumartesi";
$l['time_weekdays'] = "Zamanlama Ayarı: <span style=\"color: rgb(128, 0, 0);\">Haftalık/İş Günleri</span>";
$l['time_weekdays_desc'] = "Bu görevin çalışması için bir iş günü seçin. Çoklu iş günü seçmek için <strong>CTRL</strong> tuşunu basılı tutarak seçiminizi yapın.<br />Eğer bu görevin, her iş günü çalışmasını istiyorsanız ya da önceden tanımlı bir iş günü seçtiyseniz; <strong>''Her İş Günü''</strong> seçeneğini seçiniz.";
$l['every_month'] = "Her Ay";
$l['time_months'] = "Zamanlama Ayarı: <span style=\"color: rgb(128, 0, 0);\">Belirli Aylar</span>";
$l['time_months_desc'] = "Bu görevin çalışması için bir ay seçin. Çoklu ay seçmek için <strong>CTRL</strong> tuşunu basılı tutarak seçiminizi yapın.<br />Eğer bu görevin, her ay çalışmasını istiyorsanız ya da önceden tanımlı bir ay seçtiyseniz; <strong>''Her Ay''</strong> seçeneğini seçiniz.";
$l['enabled'] = "Görev Aktif Edilsin Mi?";
$l['enable_logging'] = "Kayıt Tutulsun Mu?";
$l['save_task'] = "Görevi Kaydet";
$l['task'] = "Görevler";
$l['date'] = "Tarih";
$l['data'] = "Veri";
$l['no_task_logs'] = "Zamanlanmış görevler için oluşturulmuş bir kayıt henüz mevcut değil.";
$l['next_run'] = "Çalışma Süresi";
$l['run_task_now'] = "Görevi Şimdi Çalıştır";
$l['disable_task'] = "Görevi Pasifleştir";
$l['run_task'] = "Görevi Çalıştır";
$l['enable_task'] = "Görevi Aktifleştir";
$l['delete_task'] = "Görevi Sil";

$l['error_invalid_task'] = "Belirtilen görev mevcut değil.";
$l['error_missing_title'] = "Zamanlanmış görev için bir başlık girmediniz.";
$l['error_missing_description'] = "Zamanlanmış görev için kısa bir bilgi girmediniz.";
$l['error_invalid_task_file'] = "Seçtiğiniz görev dosyası mevcut değil.";
$l['error_invalid_minute'] = "Girdiğiniz dakika geçersiz.";
$l['error_invalid_hour'] = "Girdiğiniz saat geçersiz.";
$l['error_invalid_day'] = "Girdiğiniz gün geçersiz.";
$l['error_invalid_weekday'] = "Girdiğiniz iş günü geçersiz.";
$l['error_invalid_month'] = "Girdiğiniz ay geçersiz.";

$l['success_task_created'] = "Görev başarıyla oluşturuldu.";
$l['success_task_updated'] = "Görev başarıyla güncellendi.";
$l['success_task_deleted'] = "Görev başarıyla silindi.";
$l['success_task_enabled'] = "Görev başarıyla aktifleştirilidi.";
$l['success_task_disabled'] = "Görev başarıyla pasifleştirildi.";
$l['success_task_run'] = "Görev başarıyla çalıştırıldı.";

$l['confirm_task_deletion'] = "Bu zamanlanmış görevi silmek istediğinizden emin misiniz?";
$l['confirm_task_enable'] = "<strong>UYARI:</strong>Sadece Cron ile çalışacak bir görev aktifleştirmektesiniz. (Lütfen, daha fazla bilgi için: <b><a href=\"https://docs.mybb.com/1.8/administration/task-manager\" target=\"_blank\" title=\"MyBB Wiki\">MyBB Wiki</a> sayfasını ziyaret ediniz.";
$l['no_tasks'] = "Forumda hiçbir zamanlanmış görev bulunamadı.";