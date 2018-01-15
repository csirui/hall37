# -*- coding=utf-8
"""
Created on 2016年9月23日

@author: zhaol
"""
import copy

from difang.majiang2.tile.tile import MTile, human_tiles
from freetime.util import log as ftlog


class MWin(object):
    """
    公共的判断和牌的AI
    """

    def __init__(self):
        super(MWin, self).__init__()

    @classmethod
    def isHu(cls, hand_tiles, magicTiles=list()):
        """
        胡牌判断，只判断手牌，杠牌，吃牌，碰牌不在内
           杠牌、吃牌、碰牌已成型，不用另外计算
        * 肯定包含将牌
        * 剩下的牌里不会有暗杠牌
        * 杠牌/吃牌/碰牌是已经成型的牌，按成型的样式计算积分，不再重新计算
        :param magicTiles 赖子牌
        :return 是否胡了
        """
        tileArr = MTile.changeTilesToValueArr(hand_tiles)
        magicArr = []
        for magicTile in magicTiles:
            magicArr.extend([magicTile for _ in range(tileArr[magicTile])])
            tileArr[magicTile] = 0

        resultArr = []
        tileTypes = [MTile.TILE_WAN, MTile.TILE_TONG, MTile.TILE_TIAO, MTile.TILE_FENG]
        hasJiang = False
        winResult = False

        for tileType in tileTypes:
            winResult, hasJiang, _tArr, _rArr, _mArr = cls.isHuWithMagic(tileArr, resultArr, magicArr, hasJiang,
                                                                         tileType)
            if not winResult:
                return False, []
            else:
                tileArr = copy.deepcopy(_tArr)
                resultArr = copy.deepcopy(_rArr)
                magicArr = copy.deepcopy(_mArr)

        if winResult and not hasJiang and len(magicArr) >= 2:
            hasJiang = True
        return hasJiang and winResult, resultArr

    @classmethod
    def isHuWithMagic(cls, tileArr, resultArr, magicArr, hasJiang, tileType):
        """

        :param tileArr:
        :param resultArr:
        :param magicArr:
        :param hasJiang:
        :param tileType:
        :return:
        """
        # 不能一次性把所有癞子都给过去，要一个一个的给，使用最少的癞子打成胡牌效果。
        # 用掉太多癞子，会导致漏和
        _hasJiang = hasJiang
        _tileArr = copy.deepcopy(tileArr)
        _resultArr = copy.deepcopy(resultArr)

        for magicLength in range(len(magicArr) + 1):
            newMagicArr = magicArr[0:magicLength]
            _newMagicArr = copy.deepcopy(newMagicArr)
            _resultType, _hasJiang = cls.isBu(_tileArr, _resultArr, newMagicArr, tileType, _hasJiang)
            # ftlog.debug('tileType:', tileType, ' resultType:', resultType, ' hasJiang:', hasJiang)
            if not _resultType:
                continue
            else:
                magicArr = magicArr[len(_newMagicArr):]
                magicArr.extend(newMagicArr)
                return _resultType, _hasJiang, _tileArr, _resultArr, magicArr

        return False, hasJiang, None, None, None

    @classmethod
    def isBu(cls, tileArr, resultArr, magicArr, tileType, hasJiang):
        """
        判断某个花色是否是三朴，缺的牌从癞子中获取，如果没有癞子牌了，也形不成三朴，和牌失败
        """
        if 0 == cls.getCardNumByType(tileArr, tileType):
            # 这个花色没有牌
            return True, hasJiang

        # ftlog.debug('check card:', MTile.traverseTile(tileType))
        for tileIndex in MTile.traverseTile(tileType):
            if tileArr[tileIndex] == 0:
                continue

            if tileArr[tileIndex] >= 3:
                # 刻，没有占用癞子
                tileArr[tileIndex] -= 3
                resultTmp, hasJiang = cls.isBu(tileArr, resultArr, magicArr, tileType, hasJiang)
                if resultTmp:
                    resultArr.append([tileIndex, tileIndex, tileIndex])
                    return True, hasJiang
                # 还原手牌，继续判断
                tileArr[tileIndex] += 3

            if (tileArr[tileIndex] == 2) and (len(magicArr) >= 1):
                # 对子，尝试加一张癞子组成刻
                tileArr[tileIndex] -= 2
                mTile = magicArr.pop(-1)
                resultTmp, hasJiang = cls.isBu(tileArr, resultArr, magicArr, tileType, hasJiang)
                if resultTmp:
                    resultArr.append([tileIndex, tileIndex, mTile])
                    return True, hasJiang

                # 还原手牌，继续判断
                tileArr[tileIndex] += 2
                magicArr.append(mTile)

            if (tileArr[tileIndex] == 1) and (len(magicArr) >= 2):
                # 单张，尝试加两张癞子组成刻
                tileArr[tileIndex] -= 1
                mTile1 = magicArr.pop(-1)
                mTile2 = magicArr.pop(-1)
                resultTmp, hasJiang = cls.isBu(tileArr, resultArr, magicArr, tileType, hasJiang)
                if resultTmp:
                    resultArr.append([tileIndex, mTile1, mTile2])
                    return True, hasJiang
                # 还原手牌，继续判断
                tileArr[tileIndex] += 1
                magicArr.append(mTile1)
                magicArr.append(mTile2)

            if not hasJiang and tileArr[tileIndex] > 0 and (tileArr[tileIndex] + len(magicArr) >= 2):
                # 凑对了
                tileArr[tileIndex] -= 1
                isMagicJiang = False
                jiangTile = tileIndex
                if tileArr[tileIndex] > 0:
                    tileArr[tileIndex] -= 1
                else:
                    isMagicJiang = True
                    jiangTile = magicArr.pop(-1)
                oldJiang = hasJiang
                # 当前的对子当将测测是否成胡
                resultTmp, hasJiang = cls.isBu(tileArr, resultArr, magicArr, tileType, True)
                if resultTmp:
                    resultArr.append([tileIndex, jiangTile])
                    hasJiang = True
                    return True, hasJiang
                else:
                    # 还原将牌标记
                    hasJiang = oldJiang

                # 还原手牌
                tileArr[tileIndex] += 1
                if isMagicJiang:
                    magicArr.append(jiangTile)
                else:
                    tileArr[tileIndex] += 1

            if tileIndex >= MTile.TILE_DONG_FENG:
                # 风箭牌不能组成顺
                return False, hasJiang

            # 提取顺牌组合
            if tileArr[tileIndex] > 0:
                # 测试顺子 0 1 2
                if MTile.getValue(tileIndex) <= 7:
                    tile0 = tileIndex
                    needMagic = 0
                    is1Magic = False
                    is2Magic = False
                    if tileArr[tileIndex + 1] == 0:
                        needMagic += 1
                        is1Magic = True
                    if tileArr[tileIndex + 2] == 0:
                        needMagic += 1
                        is2Magic = True

                    if needMagic <= len(magicArr):
                        pattern = [tile0, None, None]
                        tileArr[tileIndex] -= 1

                        if is1Magic:
                            pattern[1] = (magicArr.pop(-1))
                        else:
                            pattern[1] = (tileIndex + 1)
                            tileArr[tileIndex + 1] -= 1

                        if is2Magic:
                            pattern[2] = (magicArr.pop(-1))
                        else:
                            pattern[2] = (tileIndex + 2)
                            tileArr[tileIndex + 2] -= 1

                        resultTmp, hasJiang = cls.isBu(tileArr, resultArr, magicArr, tileType, hasJiang)
                        if resultTmp:
                            resultArr.append(pattern)
                            return True, hasJiang

                        # 还原手牌
                        tileArr[tileIndex] += 1
                        if is1Magic:
                            magicArr.append(pattern[1])
                        else:
                            tileArr[tileIndex + 1] += 1

                        if is2Magic:
                            magicArr.append(pattern[2])
                        else:
                            tileArr[tileIndex + 2] += 1

                # 测试顺子 -1 0 1
                if 8 >= MTile.getValue(tileIndex) >= 2:
                    tile1 = tileIndex
                    needMagic = 0
                    is0Magic = False
                    is2Magic = False
                    if tileArr[tileIndex - 1] == 0:
                        needMagic += 1
                        is0Magic = True
                    if tileArr[tileIndex + 1] == 0:
                        needMagic += 1
                        is2Magic = True

                    if needMagic <= len(magicArr):
                        pattern = [None, tile1, None]
                        tileArr[tileIndex] -= 1

                        if is0Magic:
                            pattern[0] = (magicArr.pop(-1))
                        else:
                            pattern[0] = (tileIndex - 1)
                            tileArr[tileIndex - 1] -= 1

                        if is2Magic:
                            pattern.append(magicArr.pop(-1))
                        else:
                            pattern.append(tileIndex + 1)
                            tileArr[tileIndex + 1] -= 1

                        resultTmp, hasJiang = cls.isBu(tileArr, resultArr, magicArr, tileType, hasJiang)
                        if resultTmp:
                            resultArr.append(pattern)
                            return True, hasJiang

                        # 还原手牌
                        tileArr[tileIndex] += 1
                        if is0Magic:
                            magicArr.append(pattern[0])
                        else:
                            tileArr[tileIndex - 1] += 1

                        if is2Magic:
                            magicArr.append(pattern[2])
                        else:
                            tileArr[tileIndex + 1] += 1

                            # 测试顺子 -2 -1 0
                if MTile.getValue(tileIndex) >= 3:
                    tile2 = tileIndex
                    needMagic = 0
                    is0Magic = False
                    is1Magic = False
                    if tileArr[tileIndex - 2] == 0:
                        needMagic += 1
                        is0Magic = True
                    if tileArr[tileIndex - 1] == 0:
                        needMagic += 1
                        is1Magic = True

                    if needMagic <= len(magicArr):
                        pattern = [None, None, tile2]
                        tileArr[tileIndex] -= 1

                        if is0Magic:
                            pattern[0] = (magicArr.pop(-1))
                        else:
                            pattern[0] = (tileIndex - 2)
                            tileArr[tileIndex - 2] -= 1

                        if is1Magic:
                            pattern[1] = (magicArr.pop(-1))
                        else:
                            pattern[1] = (tileIndex - 1)
                            tileArr[tileIndex - 1] -= 1

                        resultTmp, hasJiang = cls.isBu(tileArr, resultArr, magicArr, tileType, hasJiang)
                        if resultTmp:
                            resultArr.append(pattern)
                            return True, hasJiang

                        # 还原手牌
                        tileArr[tileIndex] += 1
                        if is0Magic:
                            magicArr.append(pattern[0])
                        else:
                            tileArr[tileIndex - 2] += 1

                        if is1Magic:
                            magicArr.append(pattern[1])
                        else:
                            tileArr[tileIndex - 1] += 1
                            # 无和牌可能
        return False, hasJiang

    @classmethod
    def _isHu(cls, tileArr, hasJiang, resultArr):
        """判断是否和牌
        参数
            tileArr： 整理好的手牌
            hasJiang： 是否有将牌
            resultArr： 结果牌
        """
        # 带判断数组中没有剩余牌了，和了
        _num = cls.getCardNum(tileArr)

        if 0 == _num:
            # 一定有将牌
            return hasJiang

        for tile in range(40):
            # 3张组合，刻
            if tileArr[tile] >= 3:
                # 去掉这三张牌
                tileArr[tile] -= 3
                # 判断剩下的牌
                if cls._isHu(tileArr, hasJiang, resultArr):
                    # 存储结果
                    pattern = [tile, tile, tile]
                    resultArr.append(pattern)
                    return True
                # 还原，继续判断
                tileArr[tile] += 3

            # 2张组合，对
            if tileArr[tile] >= 2 and not hasJiang:
                hasJiang = True
                tileArr[tile] -= 2
                if cls._isHu(tileArr, hasJiang, resultArr):
                    # 保存结果
                    pattern = [tile, tile]
                    resultArr.append(pattern)
                    return True
                # 还原
                hasJiang = False
                tileArr[tile] += 2

            # 风牌不会组成顺，不和
            if tile > 30 and hasJiang:
                """已经有将牌，只考虑顺"""
                return False

            # 提取顺牌组合
            if (tile % 10) <= 7 \
                    and tileArr[tile] > 0 \
                    and tileArr[tile + 1] > 0 \
                    and tileArr[tile + 2] > 0:
                tileArr[tile] -= 1
                tileArr[tile + 1] -= 1
                tileArr[tile + 2] -= 1

                if cls._isHu(tileArr, hasJiang, resultArr):
                    # 保存结果
                    pattern = [tile, tile + 1, tile + 2]
                    resultArr.append(pattern)
                    return True
                # 还原
                tileArr[tile] += 1
                tileArr[tile + 1] += 1
                tileArr[tile + 2] += 1

        # 无法和牌
        return False

    @classmethod
    def getCardNumByType(cls, tileArr, tileType):
        num = 0
        for tile in MTile.traverseTile(tileType):
            num += tileArr[tile]
        return num

    @classmethod
    def getCardNum(cls, tileArr):
        num = 0
        for tile in tileArr:
            num += tile
        return num


if __name__ == "__main__":
    def test():
        #     tiles = [3, 4, 5, 7, 8, 9, 17, 17]
        tiles = human_tiles("六筒 七筒 八筒 南 南 发 发 一条")
        #     ,6,7,8,3,3,3]
        result, pattern = MWin.isHu(tiles, human_tiles("一条"))
        ftlog.debug('result:', result)
        if result:
            ftlog.debug('pattern:', pattern)


    test()
