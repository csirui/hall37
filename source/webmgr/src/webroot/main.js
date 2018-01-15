var showLogViewWindow = null;
var isaddtabs = 0;

function delayLayout() {
  if (isaddtabs == 0) {
    $('#main_content').layout('collapse', 'east');
  }
  isaddtabs++;
}

$(function() {
      var openTabPanel = function(text, attributes) {
        var mt = $('#main_tabs');
        if (mt.tabs('exists', text)) {
          mt.tabs('select', text);
        } else {
          mt.tabs('add', {
                title : text,
                closable : true,
                content : '<iframe frameborder="0"  src="' + attributes.purl
                    + '" style="width:100%;height:100%;"></iframe>'
              });
        }
        if (isaddtabs == 0) {
          setTimeout(delayLayout, 1000);
        }
      };
      showLogViewWindow = function(auuid) {
        var tabtext = '运行管理';
        openTabPanel(tabtext, {
              "purl" : "model/logview/logview.html"
            });
        var selectAction = null;
        selectAction = function() {
          try {
            var logtab = $('#main_tabs').tabs('getTab', tabtext);
            if (logtab) {
              var iframes = logtab.find('iframe');
              if (iframes.length > 0) {
                var logiframe = logtab.find('iframe')[0];
                logiframe.contentWindow.selectCurrentAction(auuid);
              }
            }
          } catch (e) {
            setTimeout(selectAction, 100);
          }
        }
        setTimeout(selectAction, 100);
      }

      SS.getData(SS.url.index.modelList, {}, function(da) {
            var headInfo = {
              pokerpath : da.result.pokerpath,
              mgrpath : da.result.mgrpath,
              localip : da.result.localip.join(' -+- ')
            }
            window.headInfo = headInfo;
            document.title = da.result.title;
            new Vue({
                  el : '#main_head',
                  data : headInfo
                });

            $('#main_menu').tree({
                  data : da.result.models,
                  onSelect : function(node) {
                    if (node.attributes) {
                      openTabPanel(node.text, node.attributes);
                    }
                  }
                });
          });
    });
