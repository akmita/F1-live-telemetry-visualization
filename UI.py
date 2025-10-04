from datetime import datetime, timedelta
import pygame
import saveFiles



def main():
    print("starting main")
    ver_pos_data = saveFiles.load_object("ver_pos_data.pkl")

    # normalize dates
    # ver_pos_data.Date = data.map(lambda x: x ** 2)

    pygame.init()
    screen = pygame.display.set_mode((500, 500))
    pygame.display.set_caption("Paint Example")

    minx = min(ver_pos_data.X)
    maxx = max(ver_pos_data.X)
    miny = min(ver_pos_data.Y)
    maxy = max(ver_pos_data.Y)

    UIRange = 500

    dataRangeX = maxx - minx
    dataRangeY = maxy - miny
    rangeFactorX = UIRange / dataRangeX
    rangeFactorY = UIRange / dataRangeY

    # normalize (if neg)
    offsetX = -1 * minx
    offsetY = -1 * miny


    running = True
    drawing = False

    i = 0

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                drawing = True
            elif event.type == pygame.MOUSEBUTTONUP:
                drawing = False

        if drawing and i < ver_pos_data.__len__():
            if datetime.now() > ver_pos_data.Date[i]:
                # pos = pygame.mouse.get_pos()
                vx = (ver_pos_data.X[i].item() + offsetX) * rangeFactorX
                vy = (ver_pos_data.Y[i].item() + offsetY) * rangeFactorY

                pos = (vx,vy)
                print("drawing", pos)
                pygame.draw.circle(screen, (100, 0, 100), pos, 3)
                pygame.display.update()
                i = i + 1

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()