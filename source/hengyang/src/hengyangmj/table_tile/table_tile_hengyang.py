# -*- coding=utf-8
'''
Created on 2017年3月10日
衡阳麻将牌堆规则
只有万筒条,无字牌
@author: nick.kai.lee
'''
from test.trick_tile.trick_tile import HYTestTrickTile

from difang.majiang2.table_tile.table_tile import MTableTile
from hengyangmj.hengyang_log import HYLog


class MTableTileHengYang(MTableTile):
    def __init__(self, player_count, play_mode, run_mode):
        super(MTableTileHengYang, self).__init__(player_count, play_mode, run_mode)
        self.__tiles = []

    def send_tiles(self, active_seat_id, count):
        """
        发牌
        @param active_seat_id, 发牌对象座位号
        @param count, 获取牌的张数
        @:return 返回花色list

        PS:
        1.通过脚本热加载手段 设定HYTestTrickTile.Tiles数据
        2.self.tiles 是定义在父类中的@property
        """
        tiles = []
        if len(self.tiles) < count:
            return tiles
        if HYTestTrickTile.Debug and len(HYTestTrickTile.Tiles[active_seat_id]) >= count:
            for _ in range(count):
                tiles.append(HYTestTrickTile.Tiles[active_seat_id].pop(0))
            pass
            HYLog.debug('send_tiles: trick tiles:', tiles)

            #  手牌中要移除trick后的牌
            for tile in tiles:
                if tile in self.tiles:
                    self.tiles.remove(tile)
        else:
            for _ in range(count):
                tiles.append(self.tiles.pop(0))
            pass
            HYLog.debug('send_tiles: tiles:', tiles)
        return tiles
