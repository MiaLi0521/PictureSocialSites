$(function () {
    // AJAX请求的CSRF保护
    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            // HTTP请求方法不是GET、HEAD、OPTIONS或TRACE，并且请求是法向站内的；
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain){
                xhr.setRequestHeader('X-CSRFToken', csrf_token);
            }
        }
    });

    // 统一处理ajax error回调函数
    var default_error_message = 'Server error, please try again later.';
    // ajaxError()方法接收的第二个参数为jqXHR对象
    $(document).ajaxError(function (event, request, settings) {
        var message = null;
        if (request.responseJSON && request.responseJSON.hasOwnProperty('message')){
            message = request.responseJSON.message;
        }else if (request.responseText) {
            var IS_JSON = true;
            try {
                var data = JSON.parse(request.responseText);
            }
            catch (err) {
                IS_JSON = false;
            }
            if (IS_JSON && data !== undefined && data.hasOwnProperty('message')) {
                message = JSON.parse(request.responseText).message;
            } else {
                message = default_error_message;
            }
        }else {
            message = default_error_message;
        }
        toast(message, 'error');
    });

    // 自定义弹窗
    var flash = null;

    function toast(body, category) {
        clearTimeout(flash);
        var $toast = $('#toast');

        if (category === 'error') {
            $toast.css('background-color', 'red')
        } else {
            $toast.css('background-color', '#333')
        }

        $toast.text(body).fadeIn();
        flash = setTimeout(function () {
            $toast.fadeOut()
        }, 3000)
    }

    // 用户资料弹窗
    var hover_timer = null;

    function show_profile_popover(e){
        var $el = $(e.target);
        // setTimeout调用会返回一个唯一数作为计数器的编号
        hover_timer = setTimeout(function () {
            hover_timer = null;
            $.ajax({
                type: 'GET',
                url: $el.data('href'),
                success: function (data) {
                    $el.popover({ //初始化Bootstrap的Popover组件
                        html: true, //将内容作为html渲染
                        content: data,
                        trigger: 'manual', //默认的触发方式是单击，我们需要的是悬停，并且悬停在弹窗上仍保持弹窗显示
                        animation: false //关闭动画
                    });
                    $el.popover('show');
                    // Bootstrap插入的Popover弹窗元素使用popover类
                    $('.popover').on('mouseleave', function () {
                        setTimeout(function () {
                            $el.popover('hide');
                        }, 200);
                    });
                },
                error: function (error) {
                    toast('Server error, please try again later.')
                }
            })
        }, 500);
    }

    function fide_profile_popover(e){
        var $el = $(e.target);

        if (hover_timer){
            // 如果弹窗未显示，则清除显示弹窗的计时器，同时将hover_timer置为null
            clearTimeout(hover_timer);
            hover_timer = null;
        }else {
            setTimeout(function () {
                // 鼠标即使离开用户头像和用户名，但停留在弹窗本身时，不需要关闭弹窗
                if (!$('.popover:hover').length){
                    $el.popover('hide');
                }
            }, 200)
        }
    }

    //动态更新关注数量
    function update_followers_count(id){
        var $el = $('#followers-count-' + id);
        $.ajax({
            type: 'GET',
            url: $el.data('href'),
            success: function (data) {
                $el.text(data.count);
            }
        })
    }
    
    // 更新收藏数量
    function update_collectors_count(id) {
        $.ajax({
            type: 'GET',
            url: $('#collectors-count-' + id).data('href'),
            success: function (data) {
                $('#collectors-count-' + id).text(data.count);
            }
        });
    }

    // 30s更新一次通知消息的数量
    function update_notifications_count() {
        var $el = $('#notification-badge');
        $.ajax({
            type: 'GET',
            url: $el.data('href'),
            success: function (data) {
                if (data.count === 0){
                    $('#notification-badge').hide();
                }else {
                    $el.show();
                    $el.text(data.count);
                }
            }
        });
    }

    function follow(e){
        var $el = $(e.target);
        var id = $el.data('id');

        $.ajax({
            type: 'POST',
            url: $el.data('href'),
            success: function (data) {
                $el.prev().show();
                $el.hide();
                update_followers_count(id);
                toast(data.message);
            }
        });
    }

    function unfollow(e){
        var $el = $(e.target);
        var id = $el.data('id')

        $.ajax({
            type: 'POST',
            url: $el.data('href'),
            success: function (data) {
                $el.next().show();
                $el.hide();
                update_followers_count(id);
                toast(data.message);
            }
        });
    }

    function collect(e){
        var $el = $(e.target);
        var id = $el.data('id');

        $.ajax({
            type: 'POST',
            url: $el.data('href'),
            success: function (data) {
                $el.prev().show();
                $el.hide();
                update_collectors_count(id);
                toast(data.message);
            }
        });
    }

    function uncollect(e){
        var $el = $(e.target);
        var id = $el.data('id');

        $.ajax({
            type: 'POST',
            url: $el.data('href'),
            success: function (data) {
                $el.next().show();
                $el.hide();
                update_collectors_count(id);
                toast(data.message);
            }
        });
    }

    // 弹窗在悬停事件发生时才插入DOM元素，因为事件处理器只能绑定到已存在的元素，此处监听整个DOM
    $(document).on('click', '.follow-btn', follow.bind(this));
    $(document).on('click', '.unfollow-btn', unfollow.bind(this));
    $(document).on('click', '.uncollect-btn', uncollect.bind(this));
    $(document).on('click', '.collect-btn', collect.bind(this));

    //鼠标移入/移出用户头像和名称时的回调函数
    $('.profile-popover').hover(show_profile_popover.bind(this), fide_profile_popover.bind(this));

    // hide or show tag edit from
    $('#tag-btn').click(function () {
        $('#tags').hide();
        $('#tag-form').show();
    });
    $('#cancel-tag').click(function () {
        $('#tags').show();
        $('#tag-form').hide();
    });

    // hide or show description edit form
    $('#description-btn').click(function () {
        $('#description').hide();
        $('#description-form').show();
    });
    $('#cancel-description').click(function () {
       $('#description-form').hide();
       $('#description').show();
    });

    // delete confirm modal
    $('#confirm-delete').on('show.bs.modal', function (e) {
        $('.delete-form').attr('action', $(e.relatedTarget).data('href'))
    });

    $('#confirm-modal').on('show.bs.modal', function (e) {
        var $btn = $(e.relatedTarget); // 触发模态框的按钮
        var $modal = $(this); //模态框自己

        $modal.find('.modal-title').text($btn.data('title'));
        $modal.find('.modal-body p').text($btn.data('body'));
        $modal.find('.btn-confirm').text($btn.data('action'));
        $modal.find('form').attr('action', $btn.data('href'));
    });

    if (is_authenticated){
        setInterval(update_notifications_count, 30000);
    }

    $("[data-toggle='tooltip']").tooltip({title: moment($(this).data('timestamp')).format('lll')});
});
