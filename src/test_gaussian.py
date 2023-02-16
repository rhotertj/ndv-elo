import matplotlib.pyplot as plt
import scipy.stats
import numpy as np


# std_dev = standard deviation = sigma = sqrt(variance)

def plotGaussianDistribution(mean, std_dev, graph_color, graph_label):
    x_min = 0.0
    x_max = mean * 2

    x = np.linspace(x_min, x_max, 1000)
    y = scipy.stats.norm.pdf(x, mean, std_dev)

    plt.plot(x, y, color=graph_color, label=graph_label)
    plt.fill_between(x, y, color=graph_color, alpha=0.5)

    # plt.title('Gaussian Distribution')
    # plt.ylim(0, 2.5)
    # plt.xlabel('x')
    # plt.ylabel('Density')
    # plt.savefig("gaussian_distribution.png")
    # plt.show()

    


if __name__ == "__main__":
    # Execute only if run as a script 
    mean = 25
    std_dev = 8.3
    graph_color = "red"
    graph_label = ""
    plotGaussianDistribution(mean, std_dev, graph_color, graph_label) 
    plotGaussianDistribution(36, 2, "green", graph_label)
    plt.show()