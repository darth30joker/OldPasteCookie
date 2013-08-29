$(document).ready(function(){
	/**
	$('.tag').popover({
		trigger : 'hover',
		placement: function (tip, element) {
			var offset = $(element).offset();
			height = $(document).outerHeight();
			width = $(document).outerWidth();
			vert = 0.5 * height - offset.top;
			vertPlacement = vert > 0 ? 'bottom' : 'top';
			horiz = 0.5 * width - offset.left;
			horizPlacement = horiz > 0 ? 'right' : 'left';
			placement = Math.abs(horiz) > Math.abs(vert) ?  horizPlacement : vertPlacement;
			return placement;
		},
		delay : 500
	});
	**/
	/**
	$('.carte').popover({
		trigger : 'hover',
		placement: function (tip, element) {
			var offset = $(element).offset();
			height = $(document).outerHeight();
			width = $(document).outerWidth();
			vert = 0.5 * height - offset.top;
			vertPlacement = vert > 0 ? 'bottom' : 'top';
			horiz = 0.5 * width - offset.left;
			horizPlacement = horiz > 0 ? 'right' : 'left';
			placement = Math.abs(horiz) > Math.abs(vert) ?  horizPlacement : vertPlacement;
			return placement;
		},
		delay : 500
	});
	**/

	/** follow_unfollow statement **/
	var follow_unfollow = function(element) {
		var id = element.attr('data-id');
		$.ajax({
			data:"id=" + id,
			type:'GET',
			url:'/paste/follow',
			success:function(json) {
				if (json.result == 'fail') {
					alert(json.message);
				} else if (json.result == 'success') {
					element.hide();
					if (json.state == 'follow')
						element.prev().show();
					else if (json.state == 'unfollow')
						element.next().show();
				}
			}
		});
	};
	$('.follow').click(function() {
		follow_unfollow($(this));
	});
	/**
	$('.unfollow').click(function() {
		$('.unfollow-modal').modal('show');
		return false;
	});
	$('.unfollow-modal').find('input:eq(0)').click(function() {
		follow_unfollow($('#unfollow'));
		$('.unfollow-modal').modal('hide');
	});
	**/
	/** end of follow_unfollow statement **/

	/** favorite_unfavorite statement **/
	var favorite_unfavorite = function(element) {
		var id = element.attr('data-id');
		$.ajax({
			data:"id=" + id,
			type:'GET',
			url:'/paste/favorite',
			success:function(json) {
				if (json.result == 'fail') {
					alert(json.message);
				} else if (json.result == 'success') {
					element.hide();
					if (json.state == 'favorite')
						element.prev().show();
					else if (json.state == 'unfavorite')
						element.next().show();
				}
			}
		});
	};
	$('.favorite').click(function() {
		favorite_unfavorite($(this));
	});
	/**
	$('#unfavorite').click(function() {
		$('#unfavorite-modal').modal('show');
		return false;
	});
	$('#unfavorite-modal').find('input:eq(0)').click(function() {
		favorite_unfavorite($('#unfavorite'));
		$('#unfavorite-modal').modal('hide');
	});
	**/
	/** end of favorite_unfavorite statement **/

	/** user follow button **/
		var user_follow_unfollow = function(element) {
		var id = element.attr('data-id');
		$.ajax({
			data:"id=" + id,
			type:'GET',
			url:'/user/follow',
			success:function(json) {
				if (json.result == 'fail') {
					alert(json.message);
				} else if (json.result == 'success') {
					element.hide();
					if (json.state == 'follow')
						element.prev().show();
					else if (json.state == 'unfollow')
						element.next().show();
				}
			}
		});
	};
	$('.user-follow').click(function() {
		user_follow_unfollow($(this));
	});
	/** end of user follow **/

	$(".alert").alert();

	var paste_li_tmpl = '<li style="" class="pl10 pr10">' +
				'<div class="lh24 clearfix mb5">' +
					'<span class="lf">' +
					'<a class="mr10 fs14 fwb" href="${url}" title="${title}">${title}</a>' +
					'<span class="clc mr5">by</span>' +
					'<a class="carte fwb" href="${user_url}">${user_nickname}</a>&nbsp;&nbsp;' +
					'<span class="clc">${created_time}</span>' +
					'<span class="clc ml20">${comment_num}回复/${view_num}阅读</span>' +
					'</span>' +
					'<span class="rt clc">' +
					'<a href="javascript:void(0);" title="取消关注" class="lf clc paste-follow-link follow" data-id="${id}" {{if is_user_followed == "false"}}style="display:none;"{{/if}}><span></span>取消关注</a>' +
					'<a href="javascript:void(0);" title="关注" class="lf clc paste-follow-link follow" data-id="${id}" {{if is_user_followed == "true"}}style="display:none;"{{/if}}><span></span>关注</a>' +
					'<a href="javascript:void(0);" title="取消收藏" class="lf clc paste-favorite-link favorite" data-id="${id}" {{if is_user_favorited == "false"}}style="display:none;"{{/if}}><span></span>取消收藏</a>' +
					'<a href="javascript:void(0);" title="收藏" class="lf clc paste-favorite-link favorite" data-id="${id}" {{if is_user_followed == "true"}}style="display:none;"{{/if}}><span></span>收藏</a>' +
					'</span>' +
				'</div>' +
				'<div class="clearfix pt10">' +
					'<span class="lf tag-list-block">' +
					'{{each tags}}' +
					'<a class="tag" title="${$value.name}" href="${$value.url}">${$value.name}</a>' +
					'{{/each}}' +
					'</span>' +
					'{{if desc == ""}}<span class="no_desc">没有描述</span>' +
					'{{else}}<a href="#" class="rt show-desc-link">显示描述</a>' +
					'{{/if}}' +
				'</div>' +
				'<div class="well mt10">${desc}</div>' +
				'</li>';
	$('#more_button').click(function() {
		var page = $('#more_button').attr('_page');

		$.ajax({
			'url':'/getmore',
			'type':'POST',
			'data':'page=' + page,
			'dataType':'json',
			'success':function(data) {
				if (data.result == 'success') {
					$.each(data.pastes, function(i, item) {
						$.tmpl(paste_li_tmpl, item).appendTo('#code_list');
					});
					$('#more_button').attr('_page', parseInt(page) + 1);
					$('.follow').click(function() {
						follow_unfollow($(this));
					});
					$('.favorite').click(function() {
						favorite_unfavorite($(this));
					});
					toggle_desc();
				}
			}
		});
	});
	var toggle_desc = function() {
		$('.show-desc-link').toggle(function() {
			$(this).parents('li').find('.well').show();
			$(this).html('隐藏描述');
		}, function() {
			$(this).parents('li').find('.well').hide();
			$(this).html('显示描述');
		});
	}
	toggle_desc();
});
