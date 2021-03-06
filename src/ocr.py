import numpy as np
from box_info import BoxInfo, LineInfo, LineType
from PIL import Image, ImageDraw
import matplotlib.pyplot as plt


# TODO: test the threshold
tick_thres = 40


def read_boxes(file_path):
    boxes_str = open(file_path, mode='r').read()
    boxes_list = boxes_str.split('\n')
    boxes = [box.split(',') for box in boxes_list if len(box) != 0]

    return boxes


def find_delta(boxinfos):
    # boxes should be sorted by ascending order

    min_delta = 1000  # TODO: change to static max variable
    min_dx = 0
    min_dy = 0
    for i in range(len(boxinfos)-1):
        x0, y0 = boxinfos[i].pos
        x1, y1 = boxinfos[i+1].pos
        dx = x1 - x0
        dy = y1 - y0
        delta = np.sqrt(dx**2 + dy**2)
        if delta < min_delta:
            min_delta = delta
            min_dx = dx
            min_dy = dy

    delta_pos = np.array([min_dx, min_dy])
    return min_delta, delta_pos


def distance(p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    return np.sqrt((x2-x1)**2 + (y2-y1)**2)


def draw_boxes(path, boxinfosList, lineList):
    newimg = Image.open(path).convert('RGB')
    draw = ImageDraw.Draw(newimg)
    for line, boxinfos in zip(lineList, boxinfosList):
        print(line)
        draw.line((line.start + line.end), fill=128, width=5)
        for box in boxinfos:
            x0, y0, x1, y1 = box.box.astype(int)
            draw.rectangle([x0, y0, x1, y1], outline='black')
            # draw.text((x0+15, y0-20), str(int(line.line_dist(box))))

    plt.imshow(newimg)
    plt.show()


def tick_to_value(chart_path, box_path, axis_list):
    img = Image.open(chart_path).convert('L')
    igs = np.array(img)

    box_data = read_boxes(box_path)
    box_candidates = list(map(BoxInfo, box_data))

    dbox_list = []
    tickval_per_lines = []
    lineinfos = list(map(LineInfo, axis_list))

    ##
    visualizelistList = []
    ##
    for line in lineinfos:
        boxinfos = [box for box in box_candidates
                    if line.line_dist(box) <= tick_thres]
        boxinfos = sorted(boxinfos,
                          key=lambda box: distance(line.start, box.pos))

        if len(boxinfos) <= 1:
            tickval_per_lines.append([])
            visualizelistList.append([])
            continue
        visualizelist = []

        boxlen_list = [box.length() for box in boxinfos]
        avg_boxlen = np.max(boxlen_list, axis=0) * 1.4

        d_box, delta_pos = find_delta(boxinfos)
        d_box_avg = 0
        # print("{} -> delta {}, {}".format(len(boxinfos), d_box, delta_pos))

        tickval_list = []
        tick_pos = line.start
        # print("tick pos {}".format(tick_pos))

        curpos = boxinfos[0].pos
        # Check first element is numeric
        _, isNumeric = boxinfos[0].ocr(igs)

        dist0 = distance(tick_pos, curpos)
        # dist_offset = dist0 * 0.5
        n0 = int(dist0 // d_box)
        # print(n0)

        for i in range(n0):
            curpos = curpos - (i+1) * delta_pos
            boxinfo = BoxInfo(pos=curpos, boxlen=avg_boxlen)
            value, _ = boxinfo.ocr(igs, isNumeric)
            if value is not None:
                tickval_list.append(value)

        curpos = boxinfos[0].pos

        for cur_box in boxinfos:
            visualizelist.append(cur_box)
            value, isNumeric = cur_box.ocr(igs, isNumeric)
            tickval_list.append(value)

            dist = distance(cur_box.pos, curpos)
            n = int(dist // d_box)
            # print("dist {} curbox {} curr {} n {}".format(dist, cur_box.pos, curpos, n))
            for i in range(n - 1):
                tick_pos = tick_pos + delta_pos
                curpos = curpos + delta_pos
                boxinfo = BoxInfo(pos=curpos, boxlen=avg_boxlen)
                value, _ = boxinfo.ocr(igs, isNumeric)
                if value is not None:
                    visualizelist.append(boxinfo)
                    tickval_list.append(value)
            d_box_avg = d_box_avg + dist

            curpos = cur_box.pos

        while (True):
            curpos = curpos + delta_pos
            boxinfo = BoxInfo(pos=curpos, boxlen=avg_boxlen)
            value, _ = boxinfo.ocr(igs, isNumeric)
            if value is None:
                break
            visualizelist.append(boxinfo)
            tickval_list.append(value)

        d_box_avg = d_box_avg / (len(boxinfos) - 1)
        dbox_list.append(d_box_avg)
        tickval_per_lines.append(tickval_list)
        visualizelistList.append(visualizelist)
    # draw_boxes(chart_path, visualizelistList, lineinfos)
    print(tickval_per_lines)

    return tickval_per_lines, dbox_list
