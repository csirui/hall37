(function() {
  /**
   * @ 常用地址配置
   */
  var host = window.location.protocol + '//' + window.location.host
  var url = {
    index : {
      modelList : '/model/list'
    },
    model : {
      get_json_file : '/get/json/file',
      set_json_file : '/set/json/file',
      
      add_action : '/add/action',
      get_action_list : '/get/action/list',
      get_action_log : '/get/action/log',
      remove_action : '/remove/action',
      debug_action : '/debug/action',
      get_process_list : '/get/process/list',

      texas_gen_json_file: '/texas/gen/json/file',
      texas_get_json_file: '/texas/get/json/file',
      texas_get_match_time: '/texas/get/match/time',
      texas_precommit: '/texas/precommit',
      texas_commit: '/texas/commit',

      t3card_gen_json_file: '/t3card/gen/json/file',
      t3card_get_json_file: '/t3card/get/json/file',
      t3card_get_match_time: '/t3card/get/match/time',
      t3card_precommit: '/t3card/precommit',
      t3card_commit: '/t3card/commit',

      t3flush_gen_json_file: '/t3flush/gen/json/file',
      t3flush_get_json_file: '/t3flush/get/json/file',
      t3flush_get_match_time: '/t3flush/get/match/time',
      t3flush_precommit: '/t3flush/precommit',
      t3flush_commit: '/t3flush/commit',

      dizhu_room_list:'/dizhu/room/list',

      config: "/config"
    }
  }

  /**
   * @ 常用方法
   */
  var SanSan = window.SS = {};

  SanSan.getData = function(mod, opt, fn) {
    // 获取数据
    $.getJSON(host + mod, opt, fn)
  }

  SanSan.setData = function(mod, opt, fn) {
    // 提交数据
    $.post(host + mod, opt, fn)
  }

  SanSan.clone = function(data) {
    // 提交数据
    return JSON.parse(JSON.stringify(data));
  }

  SanSan.url = url;
  SanSan.host = host;

  /**
   * @ 路由函数，获取页面地址栏参数，转化为｛｝对象
   */
  SanSan.urlObj = function(x) {
    var re = {};
    var h = location.href;
    var l = h.indexOf(x);
    if (l <= -1) {
      return {};
    }
    h = h.substr(l + 1);
    if (!h) {
      return {};
    }
    h = h.split('&');
    var i, len = h.length, node;
    for (var i = 0; i < len; i++) {
      node = h[i];
      node = node.split('=');
      re[node[0]] = node[1] || null;
    }
    return re;
  }

  var router = function(join, data) {
    this.data = data || {};
    this.join = join || '#';
  }

  // 设置地址参数
  router.prototype.set = function(obj) {
    for (var n in obj) {
      if (obj.n === null) {
        delete this.data[n];
      } else {
        this.data[n] = obj[n];
      }
    }
    this.re();
  }
  // 获取地址参数
  router.prototype.get = function(name) {
    if (typeof name != 'string') {
      return null;
    }
    return this.data[name];
  }

  router.prototype.re = function(obj) {
    var data = obj || this.data;

    var h = '';
    for (var n in data) {
      if (h) {
        h += '&';
      }
      if (jQuery.isArray(data[n])) {
        h += n + '=' + data[n].join('|');
      } else {
        h += n + '=' + data[n];
      }
    }
    h = h ? this.join + h : '';
    h = 'http://' + window.location.host + location.pathname + h;
    if (this.join == '#') {
      window.history.pushState({}, 0, h);
    }
    if (this.join == "?") {
      window.location.href = h;
    }
  }

  window.router = function(join) {
    return new router(join, SanSan.urlObj(join));
  }

  /**
   * @ 弹出层
   */
  SanSan.dialog = function(fn) {
    var D = function(callback) {
      this.title = '';
      this.onOk = fn || function() {
      }; // 当点击确定的时候执行的方法
      this.msg = '';
      this.box = $('<div class="modal fade" id="myModal" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">\
				  <div class="modal-dialog  modal-lg">\
				    <div class="modal-content">\
				      <div class="modal-header">\
				        <button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span><span class="sr-only">Close</span></button>\
				        <h4 class="modal-title" id="myModalLabel"></h4>\
				      </div>\
				      <div class="modal-body"></div>\
				      <div class="modal-footer">\
				        <button type="button" class="btn btn-default" data-dismiss="modal">取消</button>\
				        <button type="button" class="btn btn-primary">确定</button>\
				      </div>\
				    </div>\
				  </div>\
				</div>');

      $('body').append(this.box);

      // 关闭及取消事件
      var self = this;
      $('.modal .btn-default, .modal .close').click(function() {

            $('#myModal').on('hidden.bs.modal', function() {
                  // $(this).remove();
                  // $('body').removeClass('modal-open');
                });
            self.setCss({
                  top : '0'
                });
            self.box.find('.modal-footer').show();
            $('body').removeClass('modal-open');
          });

      var self = this;
      // 确定按钮回调事件
      $('.modal .btn-primary').click(function() {
            self.onOk();
          });
    }

    // 显示
    D.prototype.show = function(str) {
      $('#myModal').modal();
      if (str) {
        this.box.find('.modal-body').html(str);
      }
      $('body').addClass('modal-open');
    }
    // 关闭
    D.prototype.hide = function(is) {
      $('#myModal').modal('hide');
      if (!is) {
        this.box.find('.modal-body').empty();
      }
    }
    // 设置正文
    D.prototype.setMsg = function(str) {
      this.box.find('.modal-body').html(str);
    }
    // 设置标题
    D.prototype.setTitle = function(str) {
      this.box.find('.modal-title').html(str);
    }

    D.prototype.setCss = function(css) {
      this.box.css(css);
    }

    D.prototype.setFooter = function() {
      this.box.find('.modal-footer').hide();
    }
    return new D(fn);
  }

})()

//function creatCommonHtml() {
//  var subhead = '<div class="container">'
//      + '<div id="headInfo">'
//      + '  <span class="title_yellow">IP地址:</span><span class="title_red">{{localip}}</span>'
//      + '  <span class="title_yellow">配置路径(poker_path):</span><span class="title_red">{{pokerpath}}</span>'
//      + '</div>' + '<nav class="collapse navbar-collapse bs-navbar-collapse">'
//      + '<ul class="nav navbar-nav" id="menu">'
//
//  if (window.location.pathname.indexOf('index.html') >= 0) {
//    subhead += '<li v-repeat="menu" class="{{$index == index ? \'active\' : \'\' }}">'
//        + '<a href="{{$index}}" v-on="click: hover">{{name}}</a>' + '</li>'
//  } else {
//    subhead += '<li v-repeat="menu" class="{{$index == index ? \'active\' : \'\' }}">'
//        + '<a href="./../../index.html#menuIndex={{$index}}">{{name}}</a></li>'
//  }
//
//  subhead += '</ul>'
//      + '&nbsp;&nbsp;&nbsp;&nbsp;<button type="button" class="btn btn-success" onclick="openLogWindown();">运行管理</button>'
//      + '</nav></div></header>';
//  document.write(subhead);
//
//  var loghtmls = [];
//  loghtmls
//      .push('<div id="action_log_win" closed="true" class="easyui-window" title="Action Window" ');
//  loghtmls
//      .push('data-options="iconCls:\'icon-save\'" style="width:800px;height:400px;padding:10px;">');
//  loghtmls.push('<div id="cc" class="easyui-layout" fit="true">');
//  loghtmls
//      .push('<div region="west" split="true" title="West" style="width:200px;">');
//  loghtmls.push('<ul id="action_log_list" class="easyui-tree"></ul>');
//  loghtmls.push('</div>');
//  loghtmls
//      .push('<div region="center" title="center title" style="padding:5px;background:#eee;">');
//  loghtmls.push('<div id="action_info">');
//  loghtmls.push('<div>ActionUUID:<span id="action_uuid"></span></div>');
//  loghtmls.push('<div>ActionTime:<span id="action_time"></span></div>');
//  loghtmls.push('<div>ActionUser:<span id="action_user"></span></div>');
//  loghtmls.push('</div>');
//  loghtmls.push('<hr>');
//  loghtmls.push('<div id="action_log">');
//  loghtmls.push('</div>');
//  loghtmls.push('</div>');
//  loghtmls.push('</div>');
//  loghtmls.push('</div>');
//  // document.write(loghtmls.join(''));
//
//}

function reloadPage() {
  $('.btn-success').hide();
  document.location.reload();
}

function openLogWindown(selectActionUuid) {
  var ele = document.getElementById('action_log_win');
  $('#action_log_win').window('open');
}

function parseIntAll(data, keys) {
  for (x in keys) {
    data[keys[x]] = parseInt(data[keys[x]]);
  }
}

Vue.filter('superInt', {
      read : function(value) {
        var v = '' + value;
        if (v.indexOf('$') >= 0) {
          return v;
        } else {
          v = parseInt(v);
          if (isNaN(v)) {
            return 0;
          }
          return v;
        }
      },
      write : function(val, oldVal) {
        var v = '' + val;
        if (v.indexOf('$') >= 0) {
          return v;
        } else {
          v = parseInt(v);
          if (isNaN(v)) {
            if (val == '') {
              return 0;
            }
            return oldVal;
          }
          return v;
        }
      }
    })

if (!String.prototype.format) {
  String.prototype.format = function() {
    var args = arguments;
    return this.replace(/{(\d+)}/g, function(match, number) { 
      return typeof args[number] != 'undefined'
        ? args[number]
        : match
      ;
    });
  };
}

function extend(destination, source) {
  for (var property in source)
    destination[property] = source[property];
  return destination;
}